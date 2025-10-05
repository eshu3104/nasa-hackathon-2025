#!/usr/bin/env python3
"""
Flask backend for Skynet Knowledge Engine
Connects frontend to semantic search, summarization, and knowledge-tree (bubble view)
"""
import os
import sys
import json
import re
from typing import List, Dict, Any
from collections import defaultdict

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from search_and_rank import SemanticSearch
from summarize_openai import summarize_documents

# Optional: use your existing embed helper (keeps consistency with your search)
try:
    from search_and_rank import embed_query_openai
except Exception:
    embed_query_openai = None

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

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

# -----------------------------
# Static pages
# -----------------------------
@app.route('/')
def serve_frontend():
    """Serve the role selection page as default"""
    return send_from_directory('frontend', 'role.html')

@app.route('/search')
def serve_search():
    """Serve the search page"""
    return send_from_directory('frontend', 'search.html')

@app.route('/track.html')
def serve_track():
    """Serve role tracking page"""
    return send_from_directory('frontend', 'track.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (images, CSS, JS)"""
    return send_from_directory('frontend', filename)

# -----------------------------
# Core search API
# -----------------------------
@app.route('/api/search', methods=['POST'])
def api_search():
    """Main search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        role = data.get('role', 'Researcher')
        top_docs = int(data.get('top_docs', 5))

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

        print(f"🔍 Searching for: '{query}' (Frontend Role: {role}, Backend Role: {backend_role})")

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

        # Generate AI summary
        try:
            print("🤖 Generating AI summary...")
            summary_results = summarize_documents(
                search_results=ranked,
                chunks_data=search_instance.chunks,
                role=backend_role,
                max_chunks_per_doc=3
            )
            ai_summary = summary_results['final_summary']
        except Exception as e:
            print(f"⚠️ Summary generation failed: {e}")
            ai_summary = f"Found {len(results)} relevant documents for your query."

        return jsonify({
            'results': results,
            'summary': ai_summary,
            'count': len(results),
            'query': query,
            'role': role
        })

    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({'error': str(e)}), 500

# -----------------------------
# Trending / Health
# -----------------------------
@app.route('/api/trending', methods=['GET'])
def api_trending():
    """Get trending/popular publications"""
    try:
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500

        trending = []
        seen_docs = set()

        # Simple sample implementation
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
        print(f"❌ Trending error: {e}")
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
                'embeddings_shape': tuple(search_instance.embeddings.shape)
            })
        else:
            return jsonify({'status': 'unhealthy', 'reason': 'Search not initialized'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'reason': str(e)}), 500

# --------------------------------------------------------------------
# Knowledge Tree (GLOBAL EXPLORER): Topic → Subtopic → … → Papers
# --------------------------------------------------------------------
# Built from existing embeddings (mean vector per paper), clustered recursively.
# Cached in-memory on first request to /api/tree.

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import threading

TREE_CACHE = {"root": None}
TREE_LOCK = threading.Lock()

# Tunables
ROOT_K = 7         # ~6–7 top categories
CHILD_K = 4        # default children per node (auto-adjusted by size)
MIN_LEAF = 20      # ≤ this many papers => stop and list papers
MAX_DEPTH = 3      # Topic -> Subtopic -> Slice -> Papers

def _paper_index(search_instance):
    """
    Build mapping: pmcid -> {idxs, vec(mean of its chunk embeddings), title, url, text_blob}
    """
    chunks = search_instance.chunks
    embs = search_instance.embeddings  # [N, D]
    by_p: Dict[str, Dict[str, Any]] = {}
    for i, c in enumerate(chunks):
        pm = str(c.get("pmcid") or c.get("doc_id") or "")
        if not pm:
            continue
        rec = by_p.setdefault(pm, {
            "idxs": [],
            "title": c.get("title", ""),
            "url": c.get("url") or c.get("paper_url") or "",
            "texts": []
        })
        rec["idxs"].append(i)
        # For labeling: use title + a bit of text
        rec["texts"].append((c.get("title") or "") + " " + (c.get("chunk_text") or "")[:400])
    # Compute mean vectors and blobs
    for pm, rec in by_p.items():
        vecs = embs[rec["idxs"], :]
        rec["vec"] = vecs.mean(axis=0)
        rec["text_blob"] = " ".join(rec["texts"])
    return by_p

def _label_cluster(pmcids, paper_map, max_terms=3):
    """Label a cluster using TF-IDF top terms from its papers."""
    docs = [paper_map[pm]["text_blob"] for pm in pmcids if pm in paper_map]
    if not docs:
        return "Cluster"
    vec = TfidfVectorizer(max_features=2000, ngram_range=(1,2), stop_words="english")
    X = vec.fit_transform(docs)
    scores = np.asarray(X.sum(axis=0)).ravel()
    terms = np.array(vec.get_feature_names_out())
    top = terms[scores.argsort()[::-1][:max_terms]]
    label = " • ".join([t.title()[:24] for t in top if len(t) > 2]) or "Cluster"
    return label

def _k_for(n, default_k):
    """Pick a reasonable K given cluster size n."""
    if n < 8:
        return 2
    return max(2, min(default_k, n // 8))

def _build_tree(search_instance):
    """
    Build full tree in memory:
      node = { id, label, size, type='topic'|'paper', children? }
    """
    paper_map = _paper_index(search_instance)
    pmcids = list(paper_map.keys())
    if not pmcids:
        return {"id": "root", "label": "No data", "size": 0, "type": "topic", "children": []}

    root = {"id": "root", "label": "Space Bioscience", "size": len(pmcids), "type": "topic", "children": []}

    def cluster_and_attach(pmcid_list: List[str], depth: int, parent: Dict[str, Any]):
        # Leaf condition: few papers or max depth
        if depth >= MAX_DEPTH or len(pmcid_list) <= MIN_LEAF:
            parent["children"] = [{
                "id": pm,
                "type": "paper",
                "label": paper_map[pm]["title"][:80] or pm,
                "size": 1,
                "paper_id": pm,
                "link": paper_map[pm]["url"]
            } for pm in pmcid_list]
            return

        # Cluster this set
        X = np.vstack([paper_map[pm]["vec"] for pm in pmcid_list])
        k = _k_for(len(pmcid_list), ROOT_K if depth == 0 else CHILD_K)
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(X)

        children = []
        for cl in range(k):
            group = [pmcid_list[i] for i, l in enumerate(labels) if l == cl]
            if not group:
                continue
            child = {
                "id": f"{parent['id']}-{depth}-{cl}",
                "type": "topic",
                "label": _label_cluster(group, paper_map),
                "size": len(group),
                "children": []
            }
            cluster_and_attach(group, depth + 1, child)
            children.append(child)

        # Largest first for nicer layout
        children.sort(key=lambda n: -n["size"])
        parent["children"] = children

    cluster_and_attach(pmcids, depth=0, parent=root)
    return root

def _get_or_build_tree():
    with TREE_LOCK:
        if TREE_CACHE.get("root") is None:
            si = get_search()
            if not si:
                return {"id": "root", "label": "Unavailable", "size": 0, "type": "topic", "children": []}
            TREE_CACHE["root"] = _build_tree(si)
        return TREE_CACHE["root"]

@app.route('/api/tree', methods=['GET'])
def api_tree_root():
    """
    Return the full Knowledge Tree (topic hierarchy down to papers).
    With ~608 papers, sending the whole tree is acceptable for hackathon UX.
    """
    try:
        tree = _get_or_build_tree()
        return jsonify(tree)
    except Exception as e:
        print("❌ Tree error:", e)
        return jsonify({"error": str(e)}), 500

# --------------------------------------------------------------------
# (Optional) Paper-level: Future-Work → Follow-up Papers (kept for later use)
# --------------------------------------------------------------------

# Hints for detecting "future work" language in Discussion/Conclusion
FW_HINTS = re.compile(
    r"\b(future work|further (study|studies|research)|remains (unclear|unknown)|"
    r"should (assess|evaluate|examine|investigate)|needed (to|for)|warrant(ed)?|"
    r"longitudinal|long-term|next steps|in the future)\b",
    re.I
)
SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')
ALLOW_SECTIONS = {"discussion", "conclusion", "limitations", "future work", "outlook"}

def _paper_chunk_indices(search_instance, pmcid: str) -> List[int]:
    return [i for i, c in enumerate(search_instance.chunks) if str(c.get("pmcid")) == str(pmcid)]

def _is_fw_chunk(c: Dict[str, Any]) -> bool:
    sec = (c.get("section") or "").strip().lower()
    if sec in ALLOW_SECTIONS and isinstance(c.get("chunk_text"), str):
        return bool(FW_HINTS.search(c["chunk_text"]))
    return False

def _extract_fw_items_from_paper(search_instance, pmcid: str, max_items: int = 12) -> List[Dict[str, Any]]:
    """Extract future-work items (sentences) from a paper's discussion/conclusion chunks."""
    items, seen = [], set()
    for i in _paper_chunk_indices(search_instance, pmcid):
        c = search_instance.chunks[i]
        if not _is_fw_chunk(c):
            continue
        text = c.get("chunk_text", "")
        for sent in SENT_SPLIT.split(text):
            if FW_HINTS.search(sent):
                label = re.sub(r"\s+", " ", sent).strip()[:180]
                key = label.lower()
                if key in seen:
                    continue
                seen.add(key)
                # simple confidence heuristic
                conf = 0.5 + 0.1 * sum(w in label.lower() for w in
                                       ["assess", "investigate", "evaluate", "unknown", "longitudinal"])
                items.append({
                    "intent_id": f"fw_{abs(hash((str(pmcid), key))) % 10**8}",
                    "label": label,
                    "score": round(min(0.95, conf), 2),
                    "raw_sentence": sent,
                    "section": c.get("section", ""),
                    "chunk_idx": i,
                })
                if len(items) >= max_items:
                    break
    return items

def _embed_query(text: str):
    """Use your existing OpenAI embedding helper if available; else raise a clear error."""
    if embed_query_openai is None:
        raise RuntimeError("embed_query_openai not available; ensure search_and_rank provides it.")
    return embed_query_openai(text)  # returns np.ndarray shape (D,)

def _aggregate_followups(search_instance, sims, exclude_pmcid: str) -> List[Dict[str, Any]]:
    """Aggregate chunk scores to per-paper results and sort."""
    by_doc: Dict[str, Dict[str, Any]] = {}
    for i, s in enumerate(sims):
        c = search_instance.chunks[i]
        if str(c.get("pmcid")) == str(exclude_pmcid):
            continue
        pmcid = str(c.get("pmcid") or c.get("doc_id") or f"doc_{i}")
        score = float(s)
        if pmcid not in by_doc or by_doc[pmcid]["relevance"] < score:
            by_doc[pmcid] = {
                "paper_id": pmcid,
                "title": c.get("title", "")[:160],
                "year": c.get("year"),
                "relevance": score,
                "evidence": (c.get("chunk_text") or "")[:180],
                "link": c.get("url") or c.get("paper_url") or "",
            }
    ranked = sorted(by_doc.values(), key=lambda r: (-r["relevance"], -(r.get("year") or 0)))
    return ranked

@app.route('/api/paper/<pmcid>/future-work', methods=['GET'])
def api_future_work(pmcid):
    """Return future-work items (labels) extracted from a paper."""
    try:
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500

        items = _extract_fw_items_from_paper(search_instance, str(pmcid))
        # provisional gap flag; UI flips it if follow-ups exist
        payload = [{
            "intent_id": it["intent_id"],
            "label": it["label"],
            "score": it["score"],
            "gap": True
        } for it in items]
        return jsonify(payload)
    except Exception as e:
        print(f"❌ Future-work error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/future-work/<intent_id>/followups', methods=['GET'])
def api_followups(intent_id):
    """Return follow-up papers for a given future-work item (by intent_id)."""
    try:
        source_pmcid = request.args.get("pmcid", "")
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500

        # recover the intent sentence by re-extracting from the source paper (MVP)
        items = _extract_fw_items_from_paper(search_instance, str(source_pmcid))
        intent = next((x for x in items if x["intent_id"] == intent_id), None)
        if not intent:
            return jsonify({"intent_id": intent_id, "followups": []})

        # embed the intent and compute cosine similarity vs all chunk embeddings
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        qv = _embed_query(intent["label"]).reshape(1, -1)  # (1, D)
        sims = cosine_similarity(search_instance.embeddings, qv).reshape(-1)  # [N]
        ranked = _aggregate_followups(search_instance, sims, exclude_pmcid=str(source_pmcid))

        # threshold to mark genuine follow-ups
        threshold = 0.32
        followups = [{
            "paper_id": r["paper_id"],
            "title": r["title"],
            "year": r.get("year"),
            "relevance": round(float(r["relevance"]), 3),
            "evidence": r["evidence"],
            "link": r["link"],
        } for r in ranked if r["relevance"] >= threshold][:12]

        return jsonify({"intent_id": intent_id, "followups": followups})
    except Exception as e:
        print(f"❌ Follow-ups error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper/<pmcid>/bubble', methods=['GET'])
def api_paper_bubble(pmcid):
    """One-shot payload for the bubble drill-down: Paper → Future-Work → Follow-ups."""
    try:
        search_instance = get_search()
        if not search_instance:
            return jsonify({'error': 'Search service not available'}), 500

        # Basic paper info
        first_chunk = next((c for c in search_instance.chunks if str(c.get("pmcid")) == str(pmcid)), None)
        if not first_chunk:
            return jsonify({'error': 'Paper not found'}), 404
        title = first_chunk.get("title", f"Paper {pmcid}")

        # FW items
        fw_items = _extract_fw_items_from_paper(search_instance, str(pmcid))
        children = []
        for it in fw_items:
            # compute follow-ups for each FW item
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            qv = _embed_query(it["label"]).reshape(1, -1)
            sims = cosine_similarity(search_instance.embeddings, qv).reshape(-1)
            ranked = _aggregate_followups(search_instance, sims, exclude_pmcid=str(pmcid))
            threshold = 0.32
            fups = [{
                "paper_id": r["paper_id"],
                "title": r["title"],
                "year": r.get("year"),
                "relevance": round(float(r["relevance"]), 3),
                "evidence": r["evidence"],
                "link": r["link"],
            } for r in ranked if r["relevance"] >= threshold][:12]

            children.append({
                "id": it["intent_id"],
                "type": "future_work",
                "label": it["label"],
                "size": max(1, int(it["score"] * 10)),
                "gap": len(fups) == 0,
                "children": [{
                    "id": f"f_{f['paper_id']}",
                    "type": "followup_paper",
                    "label": f["title"],
                    "size": max(1, int(f["relevance"] * 12)),
                    "paper_id": f["paper_id"],
                    "year": f.get("year"),
                    "evidence": f["evidence"],
                    "link": f["link"],
                } for f in fups]
            })

        # Fallback if no FW found
        if not children:
            children = [{"id": "gap", "type": "gap", "label": "No follow-ups found", "size": 1, "children": []}]

        return jsonify({
            "id": str(pmcid),
            "type": "paper",
            "label": title,
            "size": 1,
            "children": children
        })
    except Exception as e:
        print(f"❌ Bubble payload error: {e}")
        return jsonify({'error': str(e)}), 500

# -----------------------------
# Entrypoint
# -----------------------------
if __name__ == '__main__':
    print("🚀 Starting Skynet Knowledge Engine Backend...")

    # Check if we can initialize search
    search_instance = get_search()
    if not search_instance:
        print("⚠️ Warning: Search service not available. Some endpoints may not work.")

    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
