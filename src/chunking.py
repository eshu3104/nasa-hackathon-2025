# src/chunking.py
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")  # tokeniser used by OpenAI models

def chunk_text_by_tokens(text, max_tokens=800):
    if not text: return []
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunks.append(enc.decode(chunk_tokens))
    return chunks
