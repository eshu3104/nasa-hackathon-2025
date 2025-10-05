import numpy as np
import json
import random

# Load full embeddings
embeddings = np.load('models/emb_full.npy')
print('Embeddings shape:', embeddings.shape)

# Load metadata from JSONL
with open('models/emb_full_chunks.jsonl', 'r', encoding='utf8') as f:
    metadata = [json.loads(line) for line in f]
print('Total metadata entries:', len(metadata))

# Check if counts match
if embeddings.shape[0] != len(metadata):
    print('Mismatch between embeddings and metadata entries!')
else:
    print('Embedding and metadata counts match.')

# Randomly sample 3 entries
sample_indices = random.sample(range(len(metadata)), 3)
print('\nRandom samples:')
for i in sample_indices:
    print(f'\n--- Sample at index {i} ---')
    print('Metadata:')
    print(json.dumps(metadata[i], indent=2))
    print('Embedding vector (first 5 values):', embeddings[i][:5])
