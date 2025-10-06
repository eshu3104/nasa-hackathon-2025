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


def chunk_text(text, max_tokens=800):
    """Backward-compatible wrapper used by other modules.
    Delegates to chunk_text_by_tokens.
    """
    return chunk_text_by_tokens(text, max_tokens=max_tokens)


def chunk_section(text, max_tokens=2000):
    """Hybrid chunker for a section: return a single chunk if the section
    is shorter than max_tokens, otherwise split into multiple token-sized chunks.
    """
    if not text:
        return []
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        # return the whole section as one chunk
        return [text]
    # otherwise fall back to token-based slicing
    return chunk_text_by_tokens(text, max_tokens=max_tokens)
