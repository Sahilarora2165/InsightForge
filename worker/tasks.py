"""
Celery Tasks for Document Processing
"""
import os
import logging
from celery import Celery

# Initialize Celery
celery_app = Celery(
    'worker',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """
    Process a document: extract text, chunk, and generate embeddings.
    """
    # Import here to avoid circular imports
    from app.main import create_app
    from app.services.ingest import IngestService
    from app.services.rag import RAGService
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info(f"Starting document processing: {document_id}")
            
            # Process document
            ingest_service = IngestService()
            document = ingest_service.process_document(document_id)
            
            if document.status.value == 'processed':
                # Generate embeddings
                rag_service = RAGService()
                chunks = document.chunks.all()
                rag_service.embed_chunks(chunks)
                
                logger.info(f"Document processed successfully: {document_id}")
            else:
                logger.warning(f"Document processing failed: {document_id}")
            
            return {
                'document_id': document_id,
                'status': document.status.value,
                'chunk_count': document.chunk_count
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            
            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(bind=True)
def reprocess_document(self, document_id: str):
    """
    Reprocess a document (delete old data and process again).
    """
    from app.main import create_app
    from app.services.ingest import IngestService
    from app.services.rag import RAGService
    from app.models import Document, Chunk
    from app.core.database import db
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info(f"Starting document reprocessing: {document_id}")
            
            # Delete old embeddings
            rag_service = RAGService()
            rag_service.delete_document_embeddings(document_id)
            
            # Delete old chunks
            Chunk.query.filter_by(document_id=document_id).delete()
            db.session.commit()
            
            # Reprocess
            ingest_service = IngestService()
            document = ingest_service.process_document(document_id)
            
            if document.status.value == 'processed':
                # Generate new embeddings
                chunks = document.chunks.all()
                rag_service.embed_chunks(chunks)
                
                logger.info(f"Document reprocessed successfully: {document_id}")
            
            return {
                'document_id': document_id,
                'status': document.status.value,
                'chunk_count': document.chunk_count
            }
            
        except Exception as e:
            logger.error(f"Error reprocessing document {document_id}: {e}")
            raise


@celery_app.task
def cleanup_revoked_tokens():
    """
    Cleanup expired revoked tokens from the database.
    Should be run periodically (e.g., daily).
    """
    from datetime import datetime
    from app.main import create_app
    from app.models import RevokedToken
    from app.core.database import db
    
    app = create_app()
    
    with app.app_context():
        try:
            # Delete tokens that have expired
            deleted = RevokedToken.query.filter(
                RevokedToken.expires_at < datetime.utcnow()
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted} expired revoked tokens")
            return {'deleted': deleted}
            
        except Exception as e:
            logger.error(f"Error cleaning up revoked tokens: {e}")
            raise


@celery_app.task
def generate_embeddings_batch(chunk_ids: list):
    """
    Generate embeddings for a batch of chunks.
    """
    from app.main import create_app
    from app.services.rag import RAGService
    from app.models import Chunk
    
    app = create_app()
    
    with app.app_context():
        try:
            rag_service = RAGService()
            chunks = Chunk.query.filter(Chunk.id.in_(chunk_ids)).all()
            rag_service.embed_chunks(chunks)
            
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            return {'processed': len(chunks)}
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-revoked-tokens-daily': {
        'task': 'worker.tasks.cleanup_revoked_tokens',
        'schedule': 86400.0,  # 24 hours
    },
}


if __name__ == '__main__':
    celery_app.start()
