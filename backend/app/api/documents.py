"""
Documents API Routes
"""
import os
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from app.services.ingest import IngestService
from app.services.rag import RAGService
from app.core.config import settings
from app.core.security import role_required, editor_required, get_current_user_info
from app.models import DocumentStatus, Collection, CollectionMember, CollectionMemberRole, UserRole

documents_bp = Blueprint('documents', __name__)
ingest_service = IngestService()


def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in settings.allowed_extensions_list


def _user_can_upload_to_collection(collection_id: str, user_id: str, user_role: str) -> tuple:
    """
    Returns (allowed: bool, error_message: str | None, collection | None).
    Encapsulates all collection access checks for upload.
    """
    collection = Collection.query.get(collection_id)
    if not collection:
        return False, 'Collection not found', None

    if user_role == UserRole.ADMIN.value:
        return True, None, collection

    member = CollectionMember.query.filter_by(
        collection_id=collection_id,
        user_id=user_id
    ).first()

    if not member:
        return False, 'You are not a member of this collection', None

    if member.role not in (CollectionMemberRole.OWNER, CollectionMemberRole.EDITOR):
        return False, 'You need editor or owner role to upload to this collection', None

    return True, None, collection


@documents_bp.route('', methods=['POST'])
@jwt_required()
def upload_document():
    """
    Upload a document for processing.

    Accepts an optional collection_id form field.
    If provided, the document is assigned to that collection
    and the user must have editor/owner access to it.
    If not provided, the document goes to the user's default collection.
    """
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    if 'file' not in request.files:
        return jsonify({'error': 'Validation Error', 'message': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Validation Error', 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Validation Error',
            'message': f'File type not allowed. Allowed types: {", ".join(settings.allowed_extensions_list)}'
        }), 400

    # Resolve collection_id
    # collection_id can come from form data (multipart upload)
    collection_id = request.form.get('collection_id', '').strip() or None

    if collection_id:
        allowed, error_msg, collection = _user_can_upload_to_collection(collection_id, user_id, user_role)
        if not allowed:
            status = 404 if error_msg == 'Collection not found' else 403
            return jsonify({'error': 'Collection Error', 'message': error_msg}), status
    else:
        # Fall back to user's default collection
        from app.models import Collection as CollectionModel
        default_collection = CollectionModel.query.filter_by(
            created_by=user_id,
            is_default=True
        ).first()

        if default_collection:
            collection_id = default_collection.id
        # If no default collection exists yet (edge case), collection_id stays None

    filename = secure_filename(file.filename)

    try:
        document, is_duplicate = ingest_service.save_uploaded_file(
            file=file,
            filename=filename,
            user_id=user_id,
            collection_id=collection_id
        )

        if is_duplicate:
            return jsonify({
                'id': document.id,
                'filename': document.original_filename,
                'status': document.status.value,
                'collection_id': document.collection_id,
                'message': 'Document already exists (duplicate detected)'
            }), 200

        try:
            document = ingest_service.process_document(document.id)
            rag_service = RAGService()
            chunks = document.chunks.all()
            rag_service.embed_chunks(chunks)
        except Exception:
            # Status already set to FAILED inside process_document
            pass

        return jsonify({
            'id': document.id,
            'filename': document.original_filename,
            'status': document.status.value,
            'collection_id': document.collection_id,
            'message': 'Document uploaded and processing started'
        }), 201

    except Exception as e:
        return jsonify({'error': 'Upload Failed', 'message': str(e)}), 500


@documents_bp.route('', methods=['GET'])
@jwt_required()
def list_documents():
    """List documents for the current user, optionally filtered by collection."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    collection_id = request.args.get('collection_id')

    status_filter = None
    if status:
        try:
            status_filter = DocumentStatus(status)
        except ValueError:
            pass

    documents, total = ingest_service.get_documents(
        page=page,
        per_page=per_page,
        status=status_filter,
        user_id=user_id,
        collection_id=collection_id
    )

    return jsonify({
        'documents': [doc.to_dict() for doc in documents],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@documents_bp.route('/<document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id: str):
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    document = ingest_service.get_document(document_id)
    if not document:
        return jsonify({'error': 'Not Found', 'message': 'Document not found'}), 404

    if document.uploaded_by != user_id and user_role != UserRole.ADMIN.value:
        return jsonify({'error': 'Forbidden', 'message': 'You can only view your own documents'}), 403

    return jsonify(document.to_dict()), 200


@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id: str):
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    document = ingest_service.get_document(document_id)
    if not document:
        return jsonify({'error': 'Not Found', 'message': 'Document not found'}), 404

    if document.uploaded_by != user_id and user_role != UserRole.ADMIN.value:
        return jsonify({'error': 'Forbidden', 'message': 'You can only delete your own documents'}), 403

    try:
        rag_service = RAGService()
        rag_service.delete_document_embeddings(document_id)
        ingest_service.delete_document(document_id)
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Delete Failed', 'message': str(e)}), 500


@documents_bp.route('/<document_id>/download', methods=['GET'])
@jwt_required()
def download_document(document_id: str):
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')

    document = ingest_service.get_document(document_id)
    if not document:
        return jsonify({'error': 'Not Found', 'message': 'Document not found'}), 404

    if document.uploaded_by != user_id and user_role != UserRole.ADMIN.value:
        return jsonify({'error': 'Forbidden', 'message': 'You can only download your own documents'}), 403

    if not os.path.exists(document.file_path):
        return jsonify({'error': 'Not Found', 'message': 'Document file not found'}), 404

    return send_file(document.file_path, as_attachment=True, download_name=document.original_filename)


@documents_bp.route('/<document_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_document(document_id: str):
    identity = get_current_user_info()
    user_role = identity.get('role')

    if user_role not in (UserRole.ADMIN.value, UserRole.EDITOR.value):
        return jsonify({'error': 'Forbidden', 'message': 'Only editors and admins can reprocess documents'}), 403

    document = ingest_service.get_document(document_id)
    if not document:
        return jsonify({'error': 'Not Found', 'message': 'Document not found'}), 404

    try:
        rag_service = RAGService()
        rag_service.delete_document_embeddings(document_id)
        document = ingest_service.process_document(document_id)
        chunks = document.chunks.all()
        rag_service.embed_chunks(chunks)

        return jsonify({
            'id': document.id,
            'filename': document.original_filename,
            'status': document.status.value,
            'message': 'Document reprocessed successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Reprocess Failed', 'message': str(e)}), 500