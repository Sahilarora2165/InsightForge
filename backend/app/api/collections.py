"""
Collections API Routes

A Collection is a named group of documents.
Users chat scoped to one collection — answers never mix across collections.

Access rules:
- Any authenticated user can create a collection (they become owner).
- Members of a collection can list/view it.
- Only owner or admin can update/delete a collection.
- Only owner, admin, or editor-role members can upload documents to a collection.
- Viewers can only read and ask questions.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.core.database import db
from app.core.security import get_current_user_info
from app.models import (
    Collection, CollectionMember, CollectionMemberRole,
    Document, User, UserRole
)

collections_bp = Blueprint('collections', __name__)


def _get_user_membership(collection_id: str, user_id: str):
    """Return the CollectionMember row for this user, or None."""
    return CollectionMember.query.filter_by(
        collection_id=collection_id,
        user_id=user_id
    ).first()


def _can_manage(collection: Collection, user_id: str, user_role: str) -> bool:
    """True if user is admin OR is the collection owner."""
    if user_role == UserRole.ADMIN.value:
        return True
    member = _get_user_membership(collection.id, user_id)
    return member is not None and member.role == CollectionMemberRole.OWNER


def _can_upload(collection: Collection, user_id: str, user_role: str) -> bool:
    """True if user can upload documents to this collection."""
    if user_role == UserRole.ADMIN.value:
        return True
    member = _get_user_membership(collection.id, user_id)
    if member is None:
        return False
    return member.role in (CollectionMemberRole.OWNER, CollectionMemberRole.EDITOR)


def _can_read(collection: Collection, user_id: str, user_role: str) -> bool:
    """True if user is a member of this collection or an admin."""
    if user_role == UserRole.ADMIN.value:
        return True
    return _get_user_membership(collection.id, user_id) is not None


# ─── CRUD ──────────────────────────────────────────────────────────────────────

@collections_bp.route('', methods=['POST'])
@jwt_required()
def create_collection():
    """
    Create a new collection.
    The creator is automatically added as owner.
    Every user also gets a default 'My Documents' collection on first login —
    this endpoint is for named collections beyond that.
    """
    identity = get_current_user_info()
    user_id = identity.get('user_id')

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Bad Request', 'message': 'JSON body required'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Validation Error', 'message': 'name is required'}), 400
    if len(name) > 255:
        return jsonify({'error': 'Validation Error', 'message': 'name must be ≤ 255 characters'}), 400

    description = data.get('description', '').strip() or None

    collection = Collection(
        name=name,
        description=description,
        created_by=user_id,
        is_default=False
    )
    db.session.add(collection)
    db.session.flush()  # Get collection.id before adding member

    # Creator is owner
    member = CollectionMember(
        collection_id=collection.id,
        user_id=user_id,
        role=CollectionMemberRole.OWNER
    )
    db.session.add(member)
    db.session.commit()

    return jsonify(collection.to_dict(include_stats=True)), 201


@collections_bp.route('', methods=['GET'])
@jwt_required()
def list_collections():
    """
    List all collections the current user is a member of.
    Admins see all collections.
    """
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    if user_role == UserRole.ADMIN.value:
        collections = Collection.query.order_by(Collection.created_at.desc()).all()
    else:
        # Only collections where user is a member
        member_collection_ids = db.session.query(CollectionMember.collection_id).filter_by(
            user_id=user_id
        ).subquery()

        collections = Collection.query.filter(
            Collection.id.in_(member_collection_ids)
        ).order_by(Collection.created_at.desc()).all()

    return jsonify({
        'collections': [c.to_dict(include_stats=True) for c in collections],
        'total': len(collections)
    }), 200


@collections_bp.route('/<collection_id>', methods=['GET'])
@jwt_required()
def get_collection(collection_id: str):
    """Get a single collection by ID."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if not _can_read(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'You are not a member of this collection'}), 403

    return jsonify(collection.to_dict(include_stats=True)), 200


@collections_bp.route('/<collection_id>', methods=['PATCH'])
@jwt_required()
def update_collection(collection_id: str):
    """Update collection name or description. Owner or admin only."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if not _can_manage(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'Only the collection owner or admin can update it'}), 403

    data = request.get_json() or {}

    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Validation Error', 'message': 'name cannot be empty'}), 400
        if len(name) > 255:
            return jsonify({'error': 'Validation Error', 'message': 'name must be ≤ 255 characters'}), 400
        collection.name = name

    if 'description' in data:
        collection.description = data['description'].strip() or None

    collection.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(collection.to_dict(include_stats=True)), 200


@collections_bp.route('/<collection_id>', methods=['DELETE'])
@jwt_required()
def delete_collection(collection_id: str):
    """
    Delete a collection. Owner or admin only.
    Documents inside are NOT deleted — they become collection_id=NULL (uncategorized).
    """
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if collection.is_default:
        return jsonify({'error': 'Forbidden', 'message': 'Cannot delete your default collection'}), 403

    if not _can_manage(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'Only the collection owner or admin can delete it'}), 403

    # Detach documents — they go to uncategorized, not deleted
    Document.query.filter_by(collection_id=collection_id).update({'collection_id': None})
    db.session.commit()

    db.session.delete(collection)
    db.session.commit()

    return jsonify({'message': 'Collection deleted. Documents have been moved to uncategorized.'}), 200


# ─── MEMBERS ───────────────────────────────────────────────────────────────────

@collections_bp.route('/<collection_id>/members', methods=['GET'])
@jwt_required()
def list_members(collection_id: str):
    """List all members of a collection."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if not _can_read(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'You are not a member of this collection'}), 403

    members = collection.members.all()

    result = []
    for m in members:
        user = User.query.get(m.user_id)
        result.append({
            'membership_id': m.id,
            'user_id': m.user_id,
            'user_name': user.name if user else 'Unknown',
            'user_email': user.email if user else 'Unknown',
            'role': m.role.value,
            'added_at': m.added_at.isoformat()
        })

    return jsonify({'members': result, 'total': len(result)}), 200


@collections_bp.route('/<collection_id>/members', methods=['POST'])
@jwt_required()
def add_member(collection_id: str):
    """
    Add a user to a collection with a given role.
    Owner or admin only.
    Body: { "user_id": "...", "role": "editor" | "viewer" }
    """
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if not _can_manage(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'Only the collection owner or admin can add members'}), 403

    data = request.get_json() or {}
    target_user_id = data.get('user_id', '').strip()
    role_str = data.get('role', 'viewer').strip().lower()

    if not target_user_id:
        return jsonify({'error': 'Validation Error', 'message': 'user_id is required'}), 400

    # Validate role — cannot assign owner via this endpoint
    if role_str not in ('editor', 'viewer'):
        return jsonify({'error': 'Validation Error', 'message': 'role must be editor or viewer'}), 400

    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

    # Check if already a member
    existing = _get_user_membership(collection_id, target_user_id)
    if existing:
        return jsonify({'error': 'Conflict', 'message': 'User is already a member of this collection'}), 409

    role_enum = CollectionMemberRole.EDITOR if role_str == 'editor' else CollectionMemberRole.VIEWER

    member = CollectionMember(
        collection_id=collection_id,
        user_id=target_user_id,
        role=role_enum
    )
    db.session.add(member)
    db.session.commit()

    return jsonify(member.to_dict()), 201


@collections_bp.route('/<collection_id>/members/<membership_id>', methods=['DELETE'])
@jwt_required()
def remove_member(collection_id: str, membership_id: str):
    """
    Remove a member from a collection.
    Owner or admin only. Cannot remove the owner.
    """
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if not _can_manage(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'Only the collection owner or admin can remove members'}), 403

    member = CollectionMember.query.get(membership_id)
    if not member or member.collection_id != collection_id:
        return jsonify({'error': 'Not Found', 'message': 'Membership not found'}), 404

    if member.role == CollectionMemberRole.OWNER:
        return jsonify({'error': 'Forbidden', 'message': 'Cannot remove the collection owner'}), 403

    db.session.delete(member)
    db.session.commit()

    return jsonify({'message': 'Member removed from collection'}), 200


# ─── DOCUMENTS IN COLLECTION ───────────────────────────────────────────────────

@collections_bp.route('/<collection_id>/documents', methods=['GET'])
@jwt_required()
def list_collection_documents(collection_id: str):
    """List all documents in a collection."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Not Found', 'message': 'Collection not found'}), 404

    if not _can_read(collection, user_id, user_role):
        return jsonify({'error': 'Forbidden', 'message': 'You are not a member of this collection'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = Document.query.filter_by(collection_id=collection_id).order_by(Document.created_at.desc())
    total = query.count()
    documents = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'documents': [doc.to_dict() for doc in documents],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200