import os
import json
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

ROLE_SYSTEM_PROMPTS = {
    "Researcher": "You are a scientific research assistant. Summarize focusing on methods, datasets, key numerical results, and open research gaps.",
    "Funding Manager": "You are a funding analyst. Summarize focusing on impact, applications, scalability, collaborators, and any explicit funding needs.",
    "Student": "You are explaining to a student. Give simple takeaways, what was done, and why it matters."
}

def gpt5_mini_chat(messages: List[Dict[str, str]], max_tokens: int = 400, temperature: float = 0.0) -> str:
    """Chat with GPT-5-mini model for advanced reasoning and summarization."""
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Make sure it's in your .env file")
    
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def gpt4o_mini_chat(messages: List[Dict[str, str]], max_tokens: int = 400, temperature: float = 0.0) -> str:
    """Fallback chat with GPT-4o-mini model."""
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Make sure it's in your .env file")
    
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def summarize_documents_single_call(search_results: List[tuple], chunks_data: List[Dict[str, Any]], 
                                  role: str = "Researcher", max_chunks_per_doc: int = 3) -> Dict[str, Any]:
    """
    Single GPT call summarization pipeline - much faster!
    
    Args:
        search_results: List of (doc_id, doc_data) tuples from rank_docs_weighted
        chunks_data: List of chunk metadata
        role: User role for targeted summarization
        max_chunks_per_doc: Maximum chunks to use per document
    
    Returns:
        Dictionary with final summary
    """
    # Map role to available system prompts
    role_mapping = {
        "Researcher/Scientist": "Researcher",
        "Manager/Investor": "Funding Manager",
        "Researcher": "Researcher",
        "Funding Manager": "Funding Manager",
        "Student": "Student"
    }
    mapped_role = role_mapping.get(role, "Researcher")
    system_prompt = ROLE_SYSTEM_PROMPTS[mapped_role]
    
    print(f"🤖 Generating single consolidated summary for {len(search_results)} documents (Role: {mapped_role})")
    
    # Prepare all document content for single call
    documents_content = []
    doc_titles = []
    
    for doc_id, doc_data in search_results:
        # Get top chunks for this document
        top_chunks = sorted(doc_data['chunks'], key=lambda x: -x[1])[:max_chunks_per_doc]
        
        # Combine chunk texts
        chunk_texts = []
        for chunk_idx, chunk_score, section in top_chunks:
            chunk = chunks_data[chunk_idx]
            chunk_texts.append(f"[{section.upper()}] {chunk['chunk_text']}")
        
        combined_text = "\n\n".join(chunk_texts)
        doc_title = doc_data['title']
        
        documents_content.append(f"**{doc_title}**\n{combined_text}")
        doc_titles.append(doc_title)
    
    # Create single comprehensive prompt
    all_docs_text = "\n\n" + "="*80 + "\n\n".join(documents_content)
    
    user_prompt = f"""Analyze the following research documents and provide a comprehensive summary tailored for a {mapped_role}.

DOCUMENTS TO ANALYZE:
{all_docs_text}

Please provide a structured summary that includes:

1. **Key Takeaways** (5-8 main points)
2. **Methodological Insights** (if Researcher) OR **Impact & Applications** (if Funding Manager) OR **Simple Explanations** (if Student)
3. **Research Gaps & Next Steps** (if Researcher) OR **Funding Opportunities** (if Funding Manager) OR **Learning Points** (if Student)
4. **Top 3 Most Relevant Sources** (with titles and why they matter)

Be concise but comprehensive. Focus on the most important insights for a {mapped_role}."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        print(f"🤖 Calling GPT-5-mini with {len(messages[1]['content'])} characters of content...")
        # Single GPT call for everything!
        final_summary = gpt5_mini_chat(messages, max_tokens=800)
        print(f"✅ GPT-5-mini response received: {len(final_summary)} characters")
        
        return {
            'final_summary': final_summary,
            'doc_count': len(search_results),
            'role': mapped_role
        }
        
    except Exception as e:
        print(f"❌ Error in GPT-5-mini call: {e}")
        print(f"🔄 Falling back to GPT-4o-mini...")
        
        # Fallback to GPT-4o-mini
        try:
            final_summary = gpt4o_mini_chat(messages, max_tokens=800)
            print(f"✅ GPT-4o-mini fallback successful: {len(final_summary)} characters")
            
            return {
                'final_summary': final_summary,
                'doc_count': len(search_results),
                'role': mapped_role
            }
        except Exception as fallback_error:
            print(f"❌ GPT-4o-mini fallback also failed: {fallback_error}")
            # Final fallback summary
            fallback = f"Found {len(search_results)} relevant documents about your query. The top documents include: {', '.join(doc_titles[:3])}."
            return {
                'final_summary': fallback,
                'doc_count': len(search_results),
                'role': mapped_role
            }

# Legacy functions for backward compatibility
def per_doc_summary(doc_meta: Dict[str, Any], top_chunk_texts: str, role: str = "Researcher") -> str:
    """Legacy function - now redirects to single call approach."""
    return "Legacy function - use summarize_documents_single_call instead"

def final_consolidation(per_doc_summaries: List[str], role: str = "Researcher") -> str:
    """Legacy function - now redirects to single call approach."""
    return "Legacy function - use summarize_documents_single_call instead"

def summarize_documents(search_results: List[tuple], chunks_data: List[Dict[str, Any]], 
                       role: str = "Researcher", max_chunks_per_doc: int = 5) -> Dict[str, Any]:
    """
    Legacy function - now uses single call for speed.
    """
    return summarize_documents_single_call(search_results, chunks_data, role, max_chunks_per_doc)