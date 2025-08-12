import tiktoken

def chunk_text(text, max_tokens=350, overlap=50, model_name="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model_name)
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == len(tokens):
            break
        start += max_tokens - overlap
    return chunks
