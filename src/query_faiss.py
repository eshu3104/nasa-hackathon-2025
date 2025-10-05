#!/usr/bin/env python3
"""Query a FAISS index using OpenAI embeddings; requires matching metadata JSONL.
Usage: python src/query_faiss.py <faiss.index> <metadata.jsonl> "query text" [k]
"""
import sys
import numpy as np
import faiss
from openai import OpenAI
import json
from dotenv import load_dotenv
import os

# load .env so OPENAI_API_KEY is available
load_dotenv()
if not os.getenv('OPENAI_API_KEY'):
    # allow script to run but give clearer error if missing
    print('Warning: OPENAI_API_KEY not set in environment; OpenAI calls will fail.')


def embed_query_openai(text, model="text-embedding-3-small"):
    client = OpenAI()
    resp = client.embeddings.create(model=model, input=[text])
    vec = np.array(resp.data[0].embedding, dtype='float32')
    # normalize
    vec = vec / np.linalg.norm(vec)
    return vec


def query_index(index_path, metadata_path, query, k=5):
    index = faiss.read_index(index_path)
    qv = embed_query_openai(query)
    D, I = index.search(np.expand_dims(qv, axis=0), k)
    # load metadata
    meta = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            meta.append(json.loads(line))

    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        m = meta[idx]
        results.append((float(score), m))
    return results


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python src/query_faiss.py <faiss.index> <metadata.jsonl> "query" [k]')
        sys.exit(1)
    idx_path = sys.argv[1]
    meta_path = sys.argv[2]
    query = sys.argv[3]
    k = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    res = query_index(idx_path, meta_path, query, k=k)
    for score, m in res:
        print(f"score={score:.4f} pmcid={m.get('pmcid')} section={m.get('section')} title={m.get('title')}")
        print(m.get('chunk_text')[:300].replace('\n',' '))
        print('---')
