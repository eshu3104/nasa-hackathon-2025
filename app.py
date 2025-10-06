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

from search_and_rank import SemanticSearch
from summarize_openai import summarize_documents

app = Flask(__name__)
CORS(app)

# Initialize search once
search = None

def get_search():
    """Initialize and return search instance"""
    global search
    if search is None:
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

@app.route('/api/search', methods=['POST'])
def api_search():
    """Main search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        role = data.get('role', 'Researcher')
        top_docs = data.get('top_docs', 5)
        messages = data.get('messages', None)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500
        
        # Map frontend roles to backend roles
        role_mapping = {
            "Researcher/Scientist": "Researcher",
            "Investor": "Investor", 
            "Student": "Student"
        }
        
        mapped_role = role_mapping.get(role, "Researcher")
        
        # Perform search
        results = search_instance.search(
            query=query,
            role=mapped_role,
            top_k=top_docs
        )
        
        if not results:
            return jsonify({
                'response': f"I couldn't find relevant information for your query: '{query}'. Please try rephrasing your question or using different keywords.",
                'sources': [],
                'role': role
            })
        
        # Generate summary
        try:
            summary = summarize_documents(
                documents=results, 
                query=query, 
                role=mapped_role,
                messages=messages
            )
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            summary = f"Found {len(results)} relevant documents but couldn't generate summary. Error: {str(e)}"
        
        # Format sources
        sources = []
        for i, doc in enumerate(results[:top_docs], 1):
            sources.append({
                'title': f"Source {i}",
                'content': doc.get('content', '')[:500] + "..." if len(doc.get('content', '')) > 500 else doc.get('content', ''),
                'score': doc.get('score', 0),
                'url': doc.get('url', ''),
                'pmid': doc.get('pmid', '')
            })
        
        return jsonify({
            'response': summary,
            'sources': sources,
            'role': role,
            'query': query
        })
        
    except Exception as e:
        print(f"❌ Search API error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)