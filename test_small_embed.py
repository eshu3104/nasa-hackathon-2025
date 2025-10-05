#!/usr/bin/env python3
# test_small_embed.py
# Small smoke test: embed first N chunks using embed_batch from src/build_index_openai.py
from src.build_index_openai import embed_batch
import json

chunks_path = 'data/chunks.jsonl'
N = 3
texts = []
with open(chunks_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= N:
            break
        obj = json.loads(line)
        texts.append(obj.get('chunk_text', ''))

print(f'Embedding {len(texts)} texts...')
embs = embed_batch(texts, batch_size=3)
print('Done. Embeddings shape:', embs.shape)
for i, e in enumerate(embs):
    print(f'[{i}] length: {len(e)}')
