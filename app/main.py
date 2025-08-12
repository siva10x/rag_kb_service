import tempfile
from fastapi import FastAPI, Depends, UploadFile, File, Form, Body
from typing import Optional
from .auth import verify_credentials
from .kb_manager import init_kb_from_docx, search_kb
from .manifest_store import insert_metrics_row

app = FastAPI(title="Trendora KB Service", version="0.1")

@app.on_event("startup")
def startup_event():
    from .manifest_store import init_db
    init_db()

@app.get("/kb/status")
def kb_status(username: str = Depends(verify_credentials)):
    return {"status": "ok", "message": "KB service is running", "data": {}}

@app.post("/kb/init")
async def kb_init(
    file: UploadFile = File(...),
    index_version: Optional[str] = Form(None),
    username: str = Depends(verify_credentials)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    result = init_kb_from_docx(tmp_path, index_version=index_version)
    return {"status": "ok", "message": "KB initialized", "data": result}

@app.post("/kb/add")
async def kb_add(
    file: UploadFile = File(...),
    index_version: Optional[str] = Form(None),
    username: str = Depends(verify_credentials)
):
    # TODO: implement incremental add
    return {"status": "ok", "message": f"KB add started for {file.filename}"}

@app.post("/kb/search_test")
async def kb_search_test(
    query: str = Form(...),
    top_k: int = Form(3),
    username: str = Depends(verify_credentials)
):
    results = search_kb(query, top_k=top_k)
    return {
        "status": "ok",
        "message": f"Retrieved {len(results)} results for query '{query}'",
        "data": results
    }

@app.post("/metrics/log")
async def log_metrics(
    payload: dict = Body(...),
    username: str = Depends(verify_credentials)
):
    """
    Expected payload JSON:
    {
        "timestamp": "2025-08-12T16:00:00Z",
        "session_id": "sess-1",
        "query_id": "sess-1-1691846400000",
        "user_query": "What is Trendora X1?",
        "top_doc_ids": "trendora-doc-5,trendora-doc-1",
        "top_doc_scores": "0.082,0.115",
        "embedding_mean_sim": 0.91,
        "embedding_max_sim": 0.94,
        "model_answer": "The Trendora X1 ...",
        "answer_length_tokens": 42,
        "hallucination_flag": 0,
        "latency_ms": 320,
        "source_index_version": "index-20250812-153012"
    }
    """
    try:
        row = (
            payload.get("timestamp"),
            payload.get("session_id"),
            payload.get("query_id"),
            payload.get("user_query"),
            payload.get("top_doc_ids"),
            payload.get("top_doc_scores"),
            payload.get("embedding_mean_sim"),
            payload.get("embedding_max_sim"),
            payload.get("model_answer"),
            payload.get("answer_length_tokens"),
            payload.get("hallucination_flag"),
            payload.get("latency_ms"),
            payload.get("source_index_version"),
        )
        insert_metrics_row(row)
        return {"status": "ok", "message": "Metrics logged"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
