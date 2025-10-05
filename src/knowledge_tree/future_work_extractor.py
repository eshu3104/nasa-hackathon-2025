import re
from typing import Iterable, List, Dict, Any

# Export the hints so backend can reuse the compiled regex
FW_HINTS = re.compile(
    r"\b(future work|further (study|studies|research)|remains (unclear|unknown)|"
    r"should (assess|evaluate|examine|investigate)|needed (to|for)|warrant(ed)?|"
    r"longitudinal|long-term|next steps|in the future)\b",
    re.I
)

SPLIT_SENT = re.compile(r'(?<=[.!?])\s+')

ALLOW_SECTIONS = {"discussion", "conclusion", "future work", "limitations", "outlook"}

def _is_fw_chunk(c: Dict[str, Any]) -> bool:
    sec = (c.get("section") or "").strip().lower()
    if sec in ALLOW_SECTIONS and isinstance(c.get("chunk_text"), str):
        return bool(FW_HINTS.search(c["chunk_text"]))
    return False

def _normalize_label(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()[:180]

def extract_future_work_from_chunks(
    chunks: List[Dict[str, Any]],
    pmcid: str,
    max_items: int = 12,
) -> List[Dict[str, Any]]:
    """Return a list of FW items from this paper's chunks."""
    items, seen = [], set()
    for i, c in enumerate(chunks):
        if str(c.get("pmcid")) != str(pmcid):
            continue
        if not _is_fw_chunk(c):
            continue
        for sent in SPLIT_SENT.split(c["chunk_text"]):
            if FW_HINTS.search(sent):
                label = _normalize_label(sent)
                key = label.lower()
                if key in seen:
                    continue
                seen.add(key)
                # simple confidence: base + hint count
                conf = 0.5 + 0.1 * sum(w in label.lower() for w in
                    ["assess", "investigate", "evaluate", "unknown", "longitudinal"])
                items.append({
                    "intent_id": f"fw_{abs(hash((pmcid, key)))%10**8}",
                    "label": label,
                    "score": round(min(0.95, conf), 2),
                    "raw_sentence": sent,
                    "section": c.get("section", ""),
                    "chunk_idx": i,
                })
                if len(items) >= max_items:
                    break
    return items
