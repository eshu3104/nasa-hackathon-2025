# src/build_index_openai.py
import os, json, time
import numpy as np
import openai
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def embed_batch(texts, model="text-embedding-3-small", batch_size=32):
    """Embed a batch of texts using OpenAI API with rate limiting."""
    embs = []
    client = openai.OpenAI()
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"Embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} ({len(batch)} texts)")

        resp = client.embeddings.create(model=model, input=batch)
        # resp is a CreateEmbeddingResponse object; use attribute access
        embs += [d.embedding for d in resp.data]
        time.sleep(0.1)  # avoid bursts
    return np.array(embs, dtype="float32")

def build_embeddings_index(chunks_path="data/chunks.jsonl", 
                          embeddings_path="models/embeddings.npy",
                          model="text-embedding-3-small",
                          batch_size=32,
                          max_chunks=None):
    """Build embeddings index from chunks.jsonl file."""
    
    # Check if embeddings already exist
    if Path(embeddings_path).exists():
        print(f"Embeddings already exist at {embeddings_path}")
        print("Delete the file to regenerate embeddings.")
        return
    
    # Ensure API key is set
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Load chunks
    print(f"Loading chunks from {chunks_path}...")
    chunks = []
    texts = []
    
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if max_chunks is not None and len(chunks) >= int(max_chunks):
                break
            chunk = json.loads(line.strip())
            chunks.append(chunk)
            texts.append(chunk['chunk_text'])
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Create embeddings directory
    Path(embeddings_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate embeddings
    print(f"Generating embeddings using {model}...")
    embeddings = embed_batch(texts, model=model, batch_size=batch_size)
    
    # Save embeddings
    print(f"Saving embeddings to {embeddings_path}...")
    np.save(embeddings_path, embeddings)
    
    # Save chunks metadata alongside embeddings for easy retrieval
    chunks_metadata_path = embeddings_path.replace('.npy', '_chunks.jsonl')
    with open(chunks_metadata_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    print(f"Successfully created embeddings index:")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Chunks metadata: {chunks_metadata_path}")
    print(f"  Shape: {embeddings.shape}")
    
    return embeddings, chunks

def load_embeddings_index(embeddings_path="models/embeddings.npy"):
    """Load embeddings and corresponding chunks metadata."""
    chunks_metadata_path = embeddings_path.replace('.npy', '_chunks.jsonl')
    
    # Load embeddings
    embeddings = np.load(embeddings_path)
    
    # Load chunks metadata
    chunks = []
    with open(chunks_metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line.strip()))
    
    print(f"Loaded embeddings index:")
    print(f"  Embeddings shape: {embeddings.shape}")
    print(f"  Number of chunks: {len(chunks)}")
    
    return embeddings, chunks

# Example usage functions
def example_usage():
    """Example of how to use the embeddings functions."""
    
    # Build embeddings from chunks
    embeddings, chunks = build_embeddings_index(
        chunks_path="data/chunks.jsonl",
        embeddings_path="models/embeddings.npy",
        model="text-embedding-3-small"  # or "text-embedding-3-large" for higher quality
    )
    
    # Later, load embeddings for retrieval
    embeddings, chunks = load_embeddings_index("models/embeddings.npy")
    
    # Example: Get embedding for a specific chunk
    chunk_idx = 0
    chunk_embedding = embeddings[chunk_idx]
    chunk_data = chunks[chunk_idx]
    
    print(f"Chunk {chunk_idx}: {chunk_data['chunk_id']}")
    print(f"Embedding shape: {chunk_embedding.shape}")
    print(f"Text preview: {chunk_data['chunk_text'][:100]}...")

if __name__ == "__main__":
    import sys
    
    # CLI: [chunks_path] [embeddings_path] [model] [max_chunks]
    chunks_path = sys.argv[1] if len(sys.argv) > 1 else "data/chunks.jsonl"
    embeddings_path = sys.argv[2] if len(sys.argv) > 2 else "models/embeddings.npy"
    model = sys.argv[3] if len(sys.argv) > 3 else "text-embedding-3-small"
    max_chunks = int(sys.argv[4]) if len(sys.argv) > 4 else None

    build_embeddings_index(chunks_path, embeddings_path, model, batch_size=32, max_chunks=max_chunks)
