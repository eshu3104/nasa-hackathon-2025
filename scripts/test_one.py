# src/test_one.py
import os, time, argparse, json, math
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- reuse your existing parsers/chunker
from fetch_parse_pmc import fetch_and_cache, parse_sections
from chunking import chunk_section

# --- OpenAI modern client
from openai import OpenAI

def embed_openai(texts, model="text-embedding-3-small"):
    client = OpenAI()
    t0 = time.time()
    resp = client.embeddings.create(model=model, input=texts)
    dt = time.time() - t0
    vecs = [d.embedding for d in resp.data]
    print(f"[EMB] OpenAI used • model={model} • batch={len(texts)} • {dt:.2f}s")
    return np.array(vecs, dtype="float32")

def embed_query(q, model="text-embedding-3-small"):
    return embed_openai([q], model=model)[0].reshape(1, -1)

def build_chunks_for_url(url, pmcid=None, max_tokens=800):
    # pmcid for cache filename
    if not pmcid:
        import re
        m = re.search(r'(PMC\d+)', url)
        pmcid = m.group(1) if m else "PMC_TEST"

    html = fetch_and_cache(url, pmcid, outdir="models/raw_html")
    parsed = parse_sections(html)

    chunks = []
    def push(section, text):
        for ch in chunk_section(text, max_tokens=max_tokens):
            chunks.append({"section": section, "chunk_text": ch})

    if parsed.get("abstract"):
        push("abstract", parsed["abstract"])

    for sec, txt in parsed.get("sections", {}).items():
        if txt:
            push(sec, txt)

    if parsed.get("funding"):
        push("funding", parsed["funding"])
    if parsed.get("acknowledgements"):
        push("acknowledgements", parsed["acknowledgements"])

    return chunks

def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="PMC article URL, e.g. https://pmc.ncbi.nlm.nih.gov/articles/PMC4136787/")
    parser.add_argument("--query", default="microgravity effects on biology", help="test query")
    parser.add_argument("--role", default="Researcher", choices=["Researcher","Funding Manager","Student"])
    parser.add_argument("--dry-run", action="store_true", help="Run parsing/chunking only; skip OpenAI calls")
    args = parser.parse_args()

    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY missing. Put it in .env or env vars."

    print(f"[STEP 1] Build chunks for: {args.url}")
    chunks = build_chunks_for_url(args.url)
    print(f"[OK] total chunks: {len(chunks)}")

    texts = [c["chunk_text"] for c in chunks]
    sections = [c["section"] for c in chunks]

    if args.dry_run:
        print("[DRY RUN] Skipping OpenAI embedding. Summary below:")
        print(f"  Total chunks: {len(chunks)}")
        from collections import Counter
        print("  Section counts:")
        for sec, cnt in Counter(sections).most_common():
            print(f"    {sec}: {cnt}")
        print("  Example chunk preview:")
        if texts:
            print(texts[0][:400].replace('\n',' '))
        print("Dry run complete.")
        return

    print("[STEP 2] Embed chunks (OpenAI)…")
    E = embed_openai(texts)                      # shape (N, D)
    print(f"[OK] embeddings shape: {E.shape}")

    print("[STEP 3] Embed query & search…")
    qv = embed_query(args.query)                 # shape (1, D)
    sims = cosine_similarity(qv, E)[0]
    order = np.argsort(-sims)

    # simple role weight demo
    role_weights = {
        "Researcher":      {"methods":0.40, "results":0.35, "abstract":0.15, "conclusion":0.06, "funding":0.04},
        "Funding Manager": {"funding":0.50, "conclusion":0.25, "abstract":0.15, "acknowledgements":0.05, "results":0.05},
        "Student":         {"abstract":0.50, "conclusion":0.30, "results":0.15, "methods":0.05}
    }
    wmap = role_weights[args.role]
    boosted = []
    for i in order[:50]:
        sec = sections[i]
        w = 1.0 + wmap.get(sec, 0.0)
        boosted.append((i, sims[i] * w))

    boosted.sort(key=lambda x: -x[1])

    print(f"[RESULT] Top 5 chunks for role={args.role} and query='{args.query}':\n")
    for rank, (i, score) in enumerate(boosted[:5], start=1):
        preview = texts[i].strip().replace("\n", " ")
        if len(preview) > 200: preview = preview[:200] + "…"
        print(f"{rank}. section={sections[i]:<15} | score={score:.4f}")
        print(f"    {preview}\n")

    print("Smoke test complete. You just exercised: fetch → parse → chunk → OpenAI embeddings → query → role-weighted ranking.")

if __name__ == "__main__":
    main()
