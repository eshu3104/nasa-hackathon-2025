#!/usr/bin/env python3
"""Build a FAISS index from saved embeddings (.npy) and write index to disk.
Usage: python src/build_faiss.py <embeddings.npy> <faiss.index>
"""
import sys
import numpy as np
import faiss
from pathlib import Path


def build_faiss(embeddings_path, index_path, normalize=True):
    embeddings = np.load(embeddings_path)
    n, d = embeddings.shape
    print(f"Loaded embeddings {embeddings_path} shape={embeddings.shape}")

    if normalize:
        # normalize to unit vectors for cosine similarity via inner product
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

    index = faiss.IndexFlatIP(d)
    index.add(embeddings.astype('float32'))
    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, index_path)
    print(f"Saved FAISS index to {index_path} (n={n}, d={d})")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python src/build_faiss.py <embeddings.npy> <faiss.index>")
        sys.exit(1)
    emb = sys.argv[1]
    idx = sys.argv[2]
    build_faiss(emb, idx)
