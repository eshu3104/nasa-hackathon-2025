# src/summarize_openai.py
import openai, os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

ROLE_SYSTEM_PROMPTS = {
    "Researcher": "You are a scientific research assistant. Summarize focusing on methods, datasets, key numerical results, and open research gaps.",
    "Funding Manager": "You are a funding analyst. Summarize focusing on impact, applications, scalability, collaborators, and any explicit funding needs.",
    "Student": "You are explaining to a student. Give simple takeaways, what was done, and why it matters."
}

def gpt4o_mini_chat(messages: List[Dict[str, str]], max_tokens: int = 400, temperature: float = 0.0) -> str:
    """Chat with GPT-4o-mini model."""
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Make sure it's in your .env file")
    
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp['choices'][0]['message']['content'].strip()

def per_doc_summary(doc_meta: Dict[str, Any], top_chunk_texts: str, role: str = "Researcher") -> str:
    """Generate a summary for a single document based on its top chunks."""
    system = ROLE_SYSTEM_PROMPTS[role]
    prompt = f"{system}\n\nSummarize the following extracted text from a single paper into 3–6 concise bullet points. Keep it factual, include any explicit funding/grant strings if present.\n\nTEXT:\n{top_chunk_texts}"
    messages = [
        {"role": "system", "content": system}, 
        {"role": "user", "content": prompt}
    ]
    return gpt4o_mini_chat(messages, max_tokens=300)

def final_consolidation(per_doc_summaries: List[str], role: str = "Researcher") -> str:
    """Generate a final consolidated summary from multiple document summaries."""
    system = ROLE_SYSTEM_PROMPTS[role]
    concat = "\n\n".join(per_doc_summaries)
    prompt = f"{system}\n\nThe following are short summaries from relevant papers. Produce a single, structured summary tailored to the role (Researcher/Funding Manager/Student). Include: 1) 5–8 key takeaways, 2) suggested next research steps or funding recommendations (if Funding Manager), and 3) top source titles and links (2–3). Be concise."
    messages = [
        {"role": "system", "content": system}, 
        {"role": "user", "content": prompt + "\n\nSOURCE SUMMARIES:\n" + concat}
    ]
    return gpt4o_mini_chat(messages, max_tokens=500)

def summarize_documents(search_results: List[tuple], chunks_data: List[Dict[str, Any]], 
                       role: str = "Researcher", max_chunks_per_doc: int = 5) -> Dict[str, Any]:
    """
    Multi-stage summarization pipeline.
    
    Args:
        search_results: List of (doc_id, doc_data) tuples from rank_docs_weighted
        chunks_data: List of chunk metadata
        role: User role for targeted summarization
        max_chunks_per_doc: Maximum chunks to use per document
    
    Returns:
        Dictionary with per-doc summaries and final consolidation
    """
    per_doc_summaries = []
    doc_details = []
    
    print(f"Generating summaries for {len(search_results)} documents (Role: {role})")
    
    for doc_id, doc_data in search_results:
        # Get top chunks for this document
        doc_chunks = doc_data['chunks'][:max_chunks_per_doc]
        
        # Extract text from chunks
        chunk_texts = []
        for chunk_idx, score, section in doc_chunks:
            chunk = chunks_data[chunk_idx]
            chunk_texts.append(f"[{section}] {chunk['chunk_text']}")
        
        combined_text = "\n\n".join(chunk_texts)
        
        # Generate per-document summary
        print(f"Summarizing {doc_data['pmcid']}: {doc_data['title'][:50]}...")
        doc_summary = per_doc_summary(doc_data, combined_text, role)
        
        per_doc_summaries.append(doc_summary)
        doc_details.append({
            'pmcid': doc_data['pmcid'],
            'title': doc_data['title'],
            'url': doc_data['url'],
            'score': doc_data['score'],
            'summary': doc_summary
        })
    
    # Generate final consolidation
    print("Generating final consolidation...")
    final_summary = final_consolidation(per_doc_summaries, role)
    
    return {
        'role': role,
        'final_summary': final_summary,
        'document_summaries': doc_details,
        'num_documents': len(search_results)
    }

def print_summary_results(results: Dict[str, Any]):
    """Print formatted summary results."""
    print(f"\n{'='*80}")
    print(f"RESEARCH SUMMARY (Role: {results['role']})")
    print(f"{'='*80}")
    
    print(f"\nFINAL CONSOLIDATION:")
    print("-" * 40)
    print(results['final_summary'])
    
    print(f"\nDOCUMENT SUMMARIES ({results['num_documents']} documents):")
    print("-" * 40)
    
    for i, doc in enumerate(results['document_summaries'], 1):
        print(f"\n{i}. {doc['title']}")
        print(f"   PMC ID: {doc['pmcid']}")
        print(f"   Score: {doc['score']:.4f}")
        print(f"   URL: {doc['url']}")
        print(f"   Summary: {doc['summary']}")

# Example usage function
def example_usage():
    """Example of how to use the summarization functionality."""
    from src.search_and_rank import SemanticSearch
    
    # Initialize search
    search = SemanticSearch()
    
    # Get ranked documents
    doc_results = search.rank_docs_weighted(
        query="space biology effects of microgravity", 
        role="Researcher", 
        top_docs=3
    )
    
    # Generate summaries
    summary_results = summarize_documents(
        search_results=doc_results,
        chunks_data=search.chunks,
        role="Researcher",
        max_chunks_per_doc=5
    )
    
    # Print results
    print_summary_results(summary_results)

if __name__ == "__main__":
    import sys
    from src.search_and_rank import SemanticSearch
    
    if len(sys.argv) < 2:
        print("Usage: python summarize_openai.py <query> [role] [top_docs]")
        print("Example: python summarize_openai.py 'space biology' 'Researcher' 5")
        print("Roles: Researcher, Funding Manager, Student")
        sys.exit(1)
    
    query = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else 'Researcher'
    top_docs = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    # Initialize search and get documents
    search = SemanticSearch()
    doc_results = search.rank_docs_weighted(query, role=role, top_docs=top_docs)
    
    # Generate summaries
    summary_results = summarize_documents(
        search_results=doc_results,
        chunks_data=search.chunks,
        role=role,
        max_chunks_per_doc=5
    )
    
    # Print results
    print_summary_results(summary_results)
