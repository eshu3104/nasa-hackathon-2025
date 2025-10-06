#!/usr/bin/env python3
"""Embed chunks.jsonl into embeddings with checkpoints.
Usage: python src/build_index_checkpointed.py <chunks.jsonl> <out_prefix> [batch_size] [emb_checkpoint]
 - out_prefix: e.g. models/emb_full -> will create models/emb_full_part0.npy, parts, and models/emb_full_chunks.jsonl
"""
import sys, os, json, time
from pathlib import Path
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def embed_batch(client, texts, model='text-embedding-3-small'):
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


def build_index_checkpointed(chunks_path, out_prefix, batch_size=32, emb_checkpoint=1000):
    client = OpenAI()
    parts_dir = Path(out_prefix).parent
    parts_dir.mkdir(parents=True, exist_ok=True)

    # progress file
    prog_path = out_prefix + '.progress.json'
    prog = { 'processed': 0, 'parts': [] }
    if Path(prog_path).exists():
        prog = json.loads(Path(prog_path).read_text(encoding='utf-8'))
        print('Resuming from progress:', prog)

    # load chunks
    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))

    n = len(chunks)
    print(f'Loaded {n} chunks')

    # start embedding from prog['processed']
    i = prog.get('processed', 0)
    part_idx = len(prog.get('parts', []))
    emb_buffer = []
    meta_buffer = []

    while i < n:
        batch_texts = [chunks[j]['chunk_text'] for j in range(i, min(i+batch_size, n))]
        print(f'Embedding batch {i}/{n} (size {len(batch_texts)})')
        try:
            embs = embed_batch(client, batch_texts)
        except Exception as e:
            print('Embedding error, retrying in 5s', e)
            time.sleep(5)
            continue

        for evec, j in zip(embs, range(i, i+len(embs))):
            emb_buffer.append(evec)
            meta_buffer.append(chunks[j])

        i += len(batch_texts)

        # save part if buffer exceeds emb_checkpoint
        if len(emb_buffer) >= emb_checkpoint:
            part_file = f'{out_prefix}_part{part_idx}.npy'
            meta_file = f'{out_prefix}_part{part_idx}_chunks.jsonl'
            np.save(part_file, np.array(emb_buffer, dtype='float32'))
            with open(meta_file, 'w', encoding='utf-8') as mf:
                for m in meta_buffer:
                    mf.write(json.dumps(m, ensure_ascii=False) + '\n')
            prog['parts'].append({'part': part_file, 'meta': meta_file, 'count': len(emb_buffer)})
            prog['processed'] = i
            Path(prog_path).write_text(json.dumps(prog, ensure_ascii=False), encoding='utf-8')
            print('Wrote part', part_file)
            part_idx += 1
            emb_buffer = []
            meta_buffer = []

    # save remaining
    if emb_buffer:
        part_file = f'{out_prefix}_part{part_idx}.npy'
        meta_file = f'{out_prefix}_part{part_idx}_chunks.jsonl'
        np.save(part_file, np.array(emb_buffer, dtype='float32'))
        with open(meta_file, 'w', encoding='utf-8') as mf:
            for m in meta_buffer:
                mf.write(json.dumps(m, ensure_ascii=False) + '\n')
        prog['parts'].append({'part': part_file, 'meta': meta_file, 'count': len(emb_buffer)})
        prog['processed'] = i
        Path(prog_path).write_text(json.dumps(prog, ensure_ascii=False), encoding='utf-8')
        print('Wrote final part', part_file)

    print('Embedding complete. Progress file at', prog_path)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python src/build_index_checkpointed.py <chunks.jsonl> <out_prefix> [batch_size] [emb_checkpoint]')
        sys.exit(1)
    chunks = sys.argv[1]
    outp = sys.argv[2]
    bs = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    ec = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    build_index_checkpointed(chunks, outp, batch_size=bs, emb_checkpoint=ec)
