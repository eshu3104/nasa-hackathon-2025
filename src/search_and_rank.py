# src/search_and_rank.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import openai
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Role-based section weights for document ranking
ROLE_WEIGHTS = {
    'Researcher': {
        'methods': 0.4, 
        'results': 0.35, 
        'abstract': 0.15, 
        'conclusion': 0.05, 
        'funding': 0.03
    },
    'Funding Manager': {
        'funding': 0.5, 
        'conclusion': 0.25, 
        'abstract': 0.15, 
        'acknowledgements': 0.05
    },
    'Student': {
        'abstract': 0.5, 
        'conclusion': 0.3, 
        'results': 0.15
    }
}

class SemanticSearch:
    def __init__(self, embeddings_path="models/embeddings.npy"):
        """Initialize semantic search with embeddings and chunks."""
        self.embeddings_path = embeddings_path
        self.chunks_metadata_path = embeddings_path.replace('.npy', '_chunks.jsonl')
        
        # Load embeddings and chunks
        self.embeddings = np.load(embeddings_path)
        self.chunks = self._load_chunks()
        
        # Set up OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Make sure it's in your .env file")
        
        print(f"Using in-memory cosine similarity for {len(self.chunks)} chunks")
    
    def _load_chunks(self):
        """Load chunks metadata."""
        chunks = []
        with open(self.chunks_metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunks.append(json.loads(line.strip()))
        return chunks
    
    
    def embed_query_openai(self, query, model="text-embedding-3-small"):
        """Embed a query using OpenAI API."""
        resp = openai.Embedding.create(model=model, input=[query])
        return np.array(resp["data"][0]["embedding"], dtype="float32")
    
    def semantic_search(self, query, top_k=10):
        """In-memory cosine similarity search."""
        qemb = self.embed_query_openai(query)
        sims = cosine_similarity(qemb.reshape(1, -1), self.embeddings)[0]
        idx = np.argsort(-sims)[:top_k]
        return [(i, float(sims[i])) for i in idx]
    
    def get_chunk_by_index(self, idx):
        """Get chunk data by index."""
        if 0 <= idx < len(self.chunks):
            return self.chunks[idx]
        return None
    
    def search_with_metadata(self, query, top_k=10):
        """Search and return results with full chunk metadata."""
        results = self.semantic_search(query, top_k)
        
        search_results = []
        for idx, score in results:
            chunk = self.get_chunk_by_index(idx)
            if chunk:
                chunk['similarity_score'] = score
                search_results.append(chunk)
        
        return search_results
    
    def print_search_results(self, query, top_k=5):
        """Search and print formatted results."""
        results = self.search_with_metadata(query, top_k)
        
        print(f"\nSearch results for: '{query}'")
        print("=" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['similarity_score']:.4f}")
            print(f"   PMC ID: {result['pmcid']}")
            print(f"   Section: {result['section']}")
            print(f"   Title: {result['title']}")
            print(f"   Text: {result['chunk_text'][:200]}...")
            print(f"   URL: {result['url']}")
    
    def rank_docs_weighted(self, query, role='Researcher', top_docs=6, top_chunks=50):
        """Rank documents using role-weighted section scoring."""
        # Get top chunks first
        chunk_hits = self.semantic_search(query, top_k=top_chunks)
        
        # Aggregate chunks into documents with weighted scores
        doc_scores = {}
        for idx, score in chunk_hits:
            meta = self.chunks[idx]  # chunk metadata
            doc_id = meta['doc_id']
            section = meta['section']
            
            # Get weight for this role and section
            w = ROLE_WEIGHTS.get(role, {}).get(section, 0.0)
            
            # Initialize document if not seen before
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'score': 0.0, 
                    'chunks': [],
                    'title': meta['title'],
                    'pmcid': meta['pmcid'],
                    'url': meta['url']
                }
            
            # Add weighted score
            doc_scores[doc_id]['score'] += w * score
            doc_scores[doc_id]['chunks'].append((idx, score, section))
        
        # Sort by weighted score
        ranked = sorted(doc_scores.items(), key=lambda x: -x[1]['score'])[:top_docs]
        return ranked
    
    def print_doc_results(self, query, role='Researcher', top_docs=5, top_chunks=50):
        """Print formatted document-level results with role weighting."""
        results = self.rank_docs_weighted(query, role, top_docs, top_chunks)
        
        print(f"\nDocument results for: '{query}' (Role: {role})")
        print("=" * 60)
        
        for i, (doc_id, doc_data) in enumerate(results, 1):
            print(f"\n{i}. Document Score: {doc_data['score']:.4f}")
            print(f"   PMC ID: {doc_data['pmcid']}")
            print(f"   Title: {doc_data['title']}")
            print(f"   URL: {doc_data['url']}")
            print(f"   Matching chunks: {len(doc_data['chunks'])}")
            
            # Show top chunks for this document
            print("   Top chunks:")
            for j, (chunk_idx, chunk_score, section) in enumerate(doc_data['chunks'][:3]):
                chunk = self.chunks[chunk_idx]
                weight = ROLE_WEIGHTS.get(role, {}).get(section, 0.0)
                weighted_score = weight * chunk_score
                print(f"     {j+1}. [{section}] Score: {chunk_score:.3f} (w: {weight:.2f} → {weighted_score:.3f})")
                print(f"        {chunk['chunk_text'][:100]}...")

# Convenience functions for simple usage
def embed_query_openai(query, model="text-embedding-3-small"):
    """Standalone function to embed a query."""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Make sure it's in your .env file")
    
    resp = openai.Embedding.create(model=model, input=[query])
    return np.array(resp["data"][0]["embedding"], dtype="float32")

def semantic_search_simple(query, embeddings_path="models/embeddings.npy", top_k=10):
    """Simple semantic search function."""
    embeddings = np.load(embeddings_path)
    chunks_metadata_path = embeddings_path.replace('.npy', '_chunks.jsonl')
    
    # Load chunks
    chunks = []
    with open(chunks_metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line.strip()))
    
    # Search
    qemb = embed_query_openai(query)
    sims = cosine_similarity(qemb.reshape(1, -1), embeddings)[0]
    idx = np.argsort(-sims)[:top_k]
    
    return [(i, float(sims[i])) for i in idx]

# Example usage
def example_usage():
    """Example of how to use the search functionality."""
    
    # Initialize search
    search = SemanticSearch()
    
    # Simple search
    query = "space biology effects of microgravity"
    results = search.semantic_search(query, top_k=5)
    
    print(f"Found {len(results)} results for: '{query}'")
    for idx, score in results:
        chunk = search.get_chunk_by_index(idx)
        print(f"Score: {score:.4f} - {chunk['title'][:50]}...")
    
    # Search with full metadata
    results_with_meta = search.search_with_metadata(query, top_k=3)
    for result in results_with_meta:
        print(f"\nTitle: {result['title']}")
        print(f"Section: {result['section']}")
        print(f"Score: {result['similarity_score']:.4f}")
        print(f"Text: {result['chunk_text'][:100]}...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python search_and_rank.py <query> [top_k] [role] [mode]")
        print("Example: python search_and_rank.py 'space biology' 10 'Researcher' 'chunks'")
        print("Roles: Researcher, Funding Manager, Student")
        print("Modes: chunks, docs")
        sys.exit(1)
    
    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    role = sys.argv[3] if len(sys.argv) > 3 else 'Researcher'
    mode = sys.argv[4] if len(sys.argv) > 4 else 'docs'
    
    # Initialize search
    search = SemanticSearch()
    
    # Perform search based on mode
    if mode == 'chunks':
        search.print_search_results(query, top_k)
    elif mode == 'docs':
        search.print_doc_results(query, role, top_k)
    else:
        print(f"Unknown mode: {mode}. Use 'chunks' or 'docs'")
        sys.exit(1)
