"""
Ask (RAG Query) API Routes
"""
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.services.rag import RAGService
from app.schemas import AskRequest
from app.core.security import get_current_user_info

ask_bp = Blueprint('ask', __name__)


@ask_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_question():
    """Ask a question and get an AI-generated answer with citations."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    try:
        data = AskRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': e.errors()
        }), 400
    
    try:
        rag_service = RAGService()
        
        result = rag_service.ask(
            question=data.question,
            user_id=user_id,
            session_id=data.session_id,
            top_k=data.top_k,
            alpha=data.alpha
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Query Failed',
            'message': str(e)
        }), 500


@ask_bp.route('/ask/stream', methods=['POST'])
@jwt_required()
def ask_question_stream():
    """Ask a question with streaming response."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    try:
        data = AskRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid input data',
            'details': e.errors()
        }), 400
    
    def generate():
        try:
            rag_service = RAGService()
            
            # Perform search and rerank
            search_results = rag_service.hybrid_search(
                data.question,
                top_k=20,
                alpha=data.alpha
            )
            
            if not search_results:
                yield 'data: {"chunk": "I don\'t have any documents to search through.", "is_complete": true}\n\n'
                return
            
            reranked_results = rag_service.rerank(data.question, search_results, top_k=data.top_k)
            context, citations = rag_service.build_context(reranked_results)
            
            # Generate streaming response
            response_stream = rag_service.generate_answer(data.question, context, stream=True)
            
            full_response = ""
            for line in response_stream:
                if line:
                    try:
                        import json
                        data_line = json.loads(line)
                        chunk = data_line.get('response', '')
                        full_response += chunk
                        
                        yield f'data: {{"chunk": {json.dumps(chunk)}, "is_complete": false}}\n\n'
                        
                        if data_line.get('done', False):
                            # Send final message with citations
                            citations_data = [{
                                "document_id": c.document_id,
                                "document_name": c.document_name,
                                "page_number": c.page_number,
                                "paragraph_number": c.paragraph_number,
                                "text_snippet": c.text_snippet,
                                "relevance_score": c.relevance_score
                            } for c in citations]
                            
                            yield f'data: {{"chunk": "", "is_complete": true, "citations": {json.dumps(citations_data)}}}\n\n'
                    except:
                        pass
                        
        except Exception as e:
            yield f'data: {{"error": "{str(e)}", "is_complete": true}}\n\n'
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@ask_bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get chat history for the current user."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    session_id = request.args.get('session_id')
    limit = request.args.get('limit', 50, type=int)
    
    # Validate limit
    limit = min(limit, 100)
    
    try:
        rag_service = RAGService()
        history = rag_service.get_chat_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        return jsonify({
            'messages': history,
            'session_id': session_id,
            'total': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get history',
            'message': str(e)
        }), 500


@ask_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    """Get list of chat sessions for the current user."""
    identity = get_current_user_info()
    user_id = identity.get('user_id')
    
    from app.models import QAHistory
    from app.core.database import db
    from sqlalchemy import func
    
    # Get distinct sessions with first question
    sessions = db.session.query(
        QAHistory.session_id,
        func.min(QAHistory.created_at).label('started_at'),
        func.max(QAHistory.created_at).label('last_activity'),
        func.count(QAHistory.id).label('message_count'),
        func.min(QAHistory.question).label('first_question')
    ).filter(
        QAHistory.user_id == user_id
    ).group_by(
        QAHistory.session_id
    ).order_by(
        func.max(QAHistory.created_at).desc()
    ).limit(50).all()
    
    return jsonify({
        'sessions': [{
            'session_id': s.session_id,
            'started_at': s.started_at.isoformat(),
            'last_activity': s.last_activity.isoformat(),
            'message_count': s.message_count,
            'title': s.first_question[:50] + '...' if len(s.first_question) > 50 else s.first_question
        } for s in sessions]
    }), 200
