#!/usr/bin/env python3
"""
Flask backend for Skynet Knowledge Engine
Connects frontend to semantic search and summarization functionality
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from search_and_rank import SemanticSearch
from summarize_openai import summarize_documents

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("CORS_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Production configuration
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Initialize search once
search = None

def get_search():
    """Initialize and return search instance"""
    global search
    if search is None:
        try:
            search = SemanticSearch()
            logger.info(f"Search initialized with {len(search.chunks)} chunks")
        except Exception as e:
            logger.error(f"Error initializing search: {e}")
            search = None
    return search

@app.route('/')
def serve_frontend():
    """Serve the role selection page as default"""
    return send_from_directory('frontendwebsetup', 'role.html')

@app.route('/search')
def serve_search():
    """Serve the search page"""
    return send_from_directory('frontendwebsetup', 'search.html')

@app.route('/track.html')
def serve_track():
    """Serve role tracking page"""
    return send_from_directory('frontendwebsetup', 'track.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (images, CSS, JS)"""
    return send_from_directory('frontendwebsetup', filename)

@app.route('/api/search', methods=['POST'])
def api_search():
    """Main search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        role = data.get('role', 'Researcher')
        top_docs = data.get('top_docs', 5)
        messages = data.get('messages', None)  # chat history
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500
        
        # Map frontend roles to backend roles
        role_mapping = {
            "Researcher/Scientist": "Researcher",
            "Manager/Investor": "Funding Manager"
        }
        backend_role = role_mapping.get(role, "Researcher")
        
        logger.info(f"Searching for: '{query}' (Frontend Role: {role}, Backend Role: {backend_role})")
        
        # Get ranked documents
        ranked = search_instance.rank_docs_weighted(
            query=query, 
            role=backend_role, 
            top_docs=top_docs,
            top_chunks=50
        )
        
        if not ranked:
            return jsonify({
                'results': [],
                'summary': 'No documents found for your query.',
                'count': 0
            })
        
        # Format results for frontend
        results = []
        for doc_id, doc_data in ranked:
            # Get top chunks for this document
            top_chunks = sorted(doc_data['chunks'], key=lambda x: -x[1])[:3]
            
            result = {
                'id': doc_id,
                'title': doc_data['title'],
                'pmcid': doc_data['pmcid'],
                'url': doc_data['url'],
                'chunk_count': len(doc_data['chunks']),
                'top_chunks': []
            }
            
            # Add top chunk previews
            for chunk_idx, chunk_score, section in top_chunks:
                chunk = search_instance.chunks[chunk_idx]
                result['top_chunks'].append({
                    'text': chunk['chunk_text'][:200] + '...',
                    'section': section
                })
            
            results.append(result)
        
        # Generate AI summary (with chat history if provided)
        try:
            logger.info("Generating AI summary...")
            if messages:
                summary_results = summarize_documents(
                    search_results=ranked,
                    chunks_data=search_instance.chunks,
                    role=backend_role,
                    max_chunks_per_doc=3,
                    messages=messages
                )
            else:
                summary_results = summarize_documents(
                    search_results=ranked,
                    chunks_data=search_instance.chunks,
                    role=backend_role,
                    max_chunks_per_doc=3
                )
            ai_summary = summary_results['final_summary']
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Summary generation failed: {e}\n{tb}")
            ai_summary = f"Found {len(results)} relevant documents for your query.<br><span style='color:#ff8080'>Summary error: {e}</span>"
        
        # Build chat history for frontend: alternate user/assistant messages
        history = []
        if messages:
            for msg in messages:
                if msg.get('role') == 'user':
                    history.append({'role': 'user', 'content': msg.get('content', '')})
        history.append({'role': 'assistant', 'content': ai_summary})

        return jsonify({
            'results': results,
            'summary': ai_summary,
            'count': len(results),
            'query': query,
            'role': role,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/trending', methods=['GET'])
def api_trending():
    """Get trending/popular publications"""
    try:
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500
        
        # Get some sample publications from chunks
        # This is a simple implementation - you could make it smarter
        trending = []
        seen_docs = set()
        
        for chunk in search_instance.chunks[:100]:  # Sample first 100 chunks
            doc_id = chunk['doc_id']
            if doc_id not in seen_docs and len(trending) < 8:
                seen_docs.add(doc_id)
                trending.append({
                    'id': doc_id,
                    'title': chunk['title'],
                    'pmcid': chunk['pmcid'],
                    'url': chunk['url'],
                    'section': chunk['section'],
                    'preview': chunk['chunk_text'][:150] + '...'
                })
        
        return jsonify({'trending': trending})
        
    except Exception as e:
        logger.error(f"Trending error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    try:
        search_instance = get_search()
        if search_instance:
            return jsonify({
                'status': 'healthy',
                'chunks_loaded': len(search_instance.chunks),
                'embeddings_shape': search_instance.embeddings.shape
            })
        else:
            return jsonify({'status': 'unhealthy', 'reason': 'Search not initialized'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'reason': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Skynet Knowledge Engine Backend...")
    
    # Check if we can initialize search
    search_instance = get_search()
    if not search_instance:
        logger.warning("Search service not available. Some endpoints may not work.")
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Run the Flask app (for development only - use gunicorn in production)
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
