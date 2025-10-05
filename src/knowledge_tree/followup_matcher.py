from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Use your existing helper
from src.search_and_rank import embed_query_openai  # same model you already use

def _aggregate_doc_hits(
    chunks: List[Dict[str, Any]],
    sims: np.ndarray,
    exclude_pmcid: str
) -> List[Dict[str, Any]]:
    by_doc = {}
    for i, c in enumerate(chunks):
        if str(c.get("pmcid")) == str(exclude_pmcid):
            continue
        doc = str(c.get("pmcid") or c.get("doc_id") or f"doc_{i}")
        s = float(sims[i])
        if doc not in by_doc or by_doc[doc]["relevance"] < s:
            by_doc[doc] = {
                "paper_id": doc,
                "title": c.get("title", "")[:160],
                "year": c.get("year"),
                "relevance": s,
                "evidence": (c.get("chunk_text") or "")[:180],
                "link": c.get("url") or c.get("paper_url") or "",
            }
    ranked = sorted(by_doc.values(), key=lambda x: (-x["relevance"], -(x["year"] or 0)))
    return ranked

def find_followups_for_intent(
    intent_text: str,
    source_pmcid: str,
    search_instance
) -> List[Dict[str, Any]]:
    """
    search_instance must expose:
      - embeddings: np.ndarray [N, D]
      - chunks: List[Dict]
    """
    qv = embed_query_openai(intent_text).reshape(1, -1)  # (1, D)
    sims = cosine_similarity(search_instance.embeddings, qv).reshape(-1)  # [N]
    # light threshold; tune later
    threshold = 0.32
    ranked = _aggregate_doc_hits(search_instance.chunks, sims, exclude_pmcid=source_pmcid)
    return [
        {
            "paper_id": r["paper_id"],
            "title": r["title"],
            "year": r.get("year"),
            "relevance": round(float(r["relevance"]), 3),
            "evidence": r["evidence"],
            "link": r["link"],
        }
        for r in ranked if r["relevance"] >= threshold
    ][:12]
