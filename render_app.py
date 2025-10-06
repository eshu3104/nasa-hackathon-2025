#!/usr/bin/env python3
"""
Render deployment version of Flask backend
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from search_and_rank import SemanticSearch
    from summarize_openai import summarize_documents
except ImportError as e:
    print(f"Warning: Could not import search modules: {e}")
    SemanticSearch = None
    summarize_documents = None

app = Flask(__name__)
CORS(app)

# Initialize search once
search = None

def get_search():
    """Initialize and return search instance"""
    global search
    if search is None and SemanticSearch is not None:
        try:
            search = SemanticSearch()
            print(f"✅ Search initialized with {len(search.chunks)} chunks")
        except Exception as e:
            print(f"❌ Error initializing search: {e}")
            search = None
    return search

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'skynet-api'})

@app.route('/debug')
def debug_info():
    """Debug endpoint to check file availability"""
    import os
    try:
        models_dir = os.path.join(os.getcwd(), 'models')
        files = []
        if os.path.exists(models_dir):
            files = os.listdir(models_dir)
        
        return jsonify({
            'cwd': os.getcwd(),
            'models_dir_exists': os.path.exists(models_dir),
            'models_files': files,
            'search_initialized': search is not None,
            'openai_key_set': bool(os.getenv('OPENAI_API_KEY'))
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/search', methods=['POST'])
def api_search():
    """Main search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        role = data.get('role', 'Researcher')
        messages = data.get('messages', [])
        top_docs = data.get('top_docs', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get search instance
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 503
        
        # Map frontend roles to backend roles
        role_mapping = {
            'Researcher': 'Researcher',
            'Student': 'Student', 
            'Funding Manager': 'Funding Manager'
        }
        mapped_role = role_mapping.get(role, 'Researcher')
        
        # Perform search
        results = search_instance.search(
            query=query,
            role=mapped_role,
            top_k=top_docs
        )
        
        if not results:
            return jsonify({
                'summary': f"I couldn't find relevant information for your query: '{query}'. Please try rephrasing your question or using different keywords.",
                'results': [],
                'role': role
            })
        
        # Generate summary
        try:
            if summarize_documents:
                summary = summarize_documents(
                    documents=results, 
                    query=query, 
                    role=mapped_role,
                    messages=messages
                )
            else:
                summary = f"Found {len(results)} relevant documents. Summarization not available."
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            summary = f"Found {len(results)} relevant documents but couldn't generate summary. Error: {str(e)}"
        
        # Format results for frontend
        results_formatted = []
        for i, doc in enumerate(results[:top_docs], 1):
            results_formatted.append({
                'title': doc.get('title', f"Source {i}"),
                'pmcid': doc.get('pmcid', ''),
                'url': doc.get('url', ''),
                'content': doc.get('content', '')[:500] + "..." if len(doc.get('content', '')) > 500 else doc.get('content', ''),
                'score': doc.get('score', 0)
            })
        
        return jsonify({
            'summary': summary,
            'results': results_formatted,
            'role': role,
            'query': query
        })
        
    except Exception as e:
        print(f"❌ Search API error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)