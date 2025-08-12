import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import chromadb
from chromadb.config import Settings
from docx import Document
from openai import OpenAI
from .config import (
    OPENAI_API_KEY,
    CHROMA_PERSIST_DIR,
    KB_COLLECTION_NAME,
    BATCH_SIZE_EMBEDDINGS,
)
from .chunker import chunk_text
from .manifest_store import (
    insert_manifest_rows,
    insert_index_version,
    init_db,
    get_active_version,
)

# Initialize Chroma persistent client
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
collection = client.get_or_create_collection(
    name=KB_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
)

# OpenAI client
oa_client = OpenAI(api_key=OPENAI_API_KEY)


def read_docx_paragraphs(file_path):
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return paragraphs


def embed_texts(texts):
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE_EMBEDDINGS):
        batch = texts[i : i + BATCH_SIZE_EMBEDDINGS]
        resp = oa_client.embeddings.create(model="text-embedding-3-small", input=batch)
        embeddings.extend([e.embedding for e in resp.data])
    return embeddings


def init_kb_from_docx(file_path, index_version=None):
    init_db()
    if not index_version:
        index_version = f"index-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    paragraphs = read_docx_paragraphs(file_path)
    chunks_all = []
    for p in paragraphs:
        chunks = chunk_text(p)
        chunks_all.extend(chunks)
    embeddings = embed_texts(chunks_all)

    now = datetime.utcnow().isoformat()
    manifest_rows = []
    ids = []
    for i, chunk in enumerate(chunks_all):
        chunk_id = str(uuid.uuid4())
        doc_id = f"trendora-doc-{i}"
        metadata = {
            "doc_id": doc_id,
            "chunk_index": i,
            "index_version": index_version,
            "created_at": now,
        }
        ids.append(chunk_id)
        manifest_rows.append(
            (doc_id, chunk_id, i, index_version, now, json.dumps(metadata))
        )
        collection.add(
            ids=[chunk_id],
            documents=[chunk],
            metadatas=[metadata],
            embeddings=[embeddings[i]],
        )

    insert_manifest_rows(manifest_rows)
    insert_index_version(index_version, now, len(chunks_all), is_active=1)
    return {"index_version": index_version, "total_chunks": len(chunks_all)}


def search_kb(query_text, top_k=3):
    active_version = get_active_version()
    if not active_version:
        return []

    # Embed the query
    query_embedding = oa_client.embeddings.create(
        model="text-embedding-3-small",
        input=[query_text]
    ).data[0].embedding

    # Search Chroma with filter for active index version
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"index_version": active_version}
    )

    # Format results
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "doc_id": results["metadatas"][0][i].get("doc_id"),
            "chunk_text": results["documents"][0][i],
            "score": results["distances"][0][i],
            "metadata": results["metadatas"][0][i]
        })
    return hits