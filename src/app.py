# src/app.py
import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_and_rank import SemanticSearch
from summarize_openai import per_doc_summary, final_consolidation

st.title("Space Biology Knowledge Engine — MVP")

# Initialize search and get global variables
@st.cache_resource
def load_search():
    try:
        search = SemanticSearch()
        return search, search.chunks
    except FileNotFoundError as e:
        if "embeddings.npy" in str(e):
            return None, None
        raise

search, chunks = load_search()

if search is None:
    st.error("⚠️ Search index not found! Please run the setup commands first.")
    st.markdown("""
    **Setup required:**
    1. `python src/build_chunks.py`
    2. `python src/build_index_openai.py`
    3. Set `OPENAI_API_KEY` environment variable
    """)
else:
    # Create doc_index for easy lookup
    doc_index = {}
    for chunk in chunks:
        doc_id = chunk['doc_id']
        if doc_id not in doc_index:
            doc_index[doc_id] = {
                'title': chunk['title'],
                'url': chunk['url'],
                'pmcid': chunk['pmcid']
            }

    role = st.selectbox("I am a...", ["Researcher","Funding Manager","Student"])
    query = st.text_input("Search for...")

    if st.button("Search"):
        with st.spinner("Searching..."):
            ranked = search.rank_docs_weighted(query, role=role, top_docs=5)
        
        per_doc_summ = []
        for doc_id, info in ranked:
            # get top chunk texts for doc
            top_chunks = sorted(info['chunks'], key=lambda x: -x[1])[:3]
            top_texts = "\n\n".join([chunks[idx]['chunk_text'] for idx, _, _ in top_chunks])
            
            # Get doc_meta from first chunk
            first_chunk = chunks[top_chunks[0][0]]
            doc_meta = {
                'title': first_chunk['title'],
                'pmcid': first_chunk['pmcid'],
                'url': first_chunk['url']
            }
            
            s = per_doc_summary(doc_meta, top_texts, role=role)
            per_doc_summ.append(f"**{chunks[top_chunks[0][0]]['title']}**\n{s}")
        
        final = final_consolidation(per_doc_summ, role=role)
        st.header("AI Summary")
        st.write(final)
        st.header("Source documents used")
        for doc_id, info in ranked:
            st.write(f"- {doc_index[doc_id]['title']} — score {info['score']:.3f}")
            st.markdown(f"[View paper]({doc_index[doc_id]['url']})")