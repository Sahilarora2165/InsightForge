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
from app.models import DocumentStatus

documents_bp = Blueprint('documents', __name__)
ingest_service = IngestService()


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in settings.allowed_extensions_list


@documents_bp.route('', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload a document for processing."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    # Check if file was provided
    if 'file' not in request.files:
        return jsonify({
            'error': 'Validation Error',
            'message': 'No file provided'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'error': 'Validation Error',
            'message': 'No file selected'
        }), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Validation Error',
            'message': f'File type not allowed. Allowed types: {", ".join(settings.allowed_extensions_list)}'
        }), 400
    
    # Secure the filename
    filename = secure_filename(file.filename)
    
    try:
        # Save file and create document record
        document, is_duplicate = ingest_service.save_uploaded_file(
            file=file,
            filename=filename,
            user_id=user_id
        )
        
        if is_duplicate:
            return jsonify({
                'id': document.id,
                'filename': document.original_filename,
                'status': document.status.value,
                'message': 'Document already exists (duplicate detected)'
            }), 200
        
        # Trigger async processing (in production, use Celery)
        # For now, process synchronously
        from app.services.rag import RAGService
        try:
            document = ingest_service.process_document(document.id)
            
            # Generate embeddings
            rag_service = RAGService()
            chunks = document.chunks.all()
            rag_service.embed_chunks(chunks)
            
        except Exception as e:
            # Document status is set to FAILED in process_document
            pass
        
        return jsonify({
            'id': document.id,
            'filename': document.original_filename,
            'status': document.status.value,
            'message': 'Document uploaded and processing started'
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': 'Upload Failed',
            'message': str(e)
        }), 500


@documents_bp.route('', methods=['GET'])
@jwt_required()
def list_documents():
    """List documents for the current user."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    # Validate per_page
    per_page = min(per_page, 100)
    
    # Parse status filter
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
        user_id=user_id
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
    """Get a document by ID (only if owned by current user)."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')
    
    document = ingest_service.get_document(document_id)
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': 'Document not found'
        }), 404
    
    # Only allow access to own documents (admins can see all)
    if document.uploaded_by != user_id and user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'You can only view your own documents'
        }), 403
    
    return jsonify(document.to_dict()), 200


@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id: str):
    """Delete a document (only own documents, admins can delete any)."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')
    
    document = ingest_service.get_document(document_id)
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': 'Document not found'
        }), 404
    
    # Users can only delete their own documents, admins can delete any
    if document.uploaded_by != user_id and user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'You can only delete your own documents'
        }), 403
    
    try:
        # Delete embeddings first
        rag_service = RAGService()
        rag_service.delete_document_embeddings(document_id)
        
        # Delete document
        ingest_service.delete_document(document_id)
        
        return jsonify({
            'message': 'Document deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Delete Failed',
            'message': str(e)
        }), 500


@documents_bp.route('/<document_id>/download', methods=['GET'])
@jwt_required()
def download_document(document_id: str):
    """Download a document file (only own documents)."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    user_role = identity.get('role')
    
    document = ingest_service.get_document(document_id)
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': 'Document not found'
        }), 404
    
    # Users can only download their own documents, admins can download any
    if document.uploaded_by != user_id and user_role != 'admin':
        return jsonify({
            'error': 'Forbidden',
            'message': 'You can only download your own documents'
        }), 403
    
    if not os.path.exists(document.file_path):
        return jsonify({
            'error': 'Not Found',
            'message': 'Document file not found'
        }), 404
    
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.original_filename
    )


@documents_bp.route('/<document_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_document(document_id: str):
    """Reprocess a document."""
    identity = get_current_user_info()
    user_role = identity.get('role')
    
    # Check permission
    if user_role not in ['admin', 'editor']:
        return jsonify({
            'error': 'Forbidden',
            'message': 'Only editors and admins can reprocess documents'
        }), 403
    
    document = ingest_service.get_document(document_id)
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': 'Document not found'
        }), 404
    
    try:
        # Delete old embeddings
        rag_service = RAGService()
        rag_service.delete_document_embeddings(document_id)
        
        # Reprocess document
        document = ingest_service.process_document(document_id)
        
        # Generate new embeddings
        chunks = document.chunks.all()
        rag_service.embed_chunks(chunks)
        
        return jsonify({
            'id': document.id,
            'filename': document.original_filename,
            'status': document.status.value,
            'message': 'Document reprocessed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Reprocess Failed',
            'message': str(e)
        }), 500
