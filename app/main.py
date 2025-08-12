import json
import tempfile
import warnings
from fastapi import FastAPI, Depends, UploadFile, File, Form, Body, Query, APIRouter
from typing import Optional
from .auth import verify_credentials
from .kb_manager import init_kb_from_docx, search_kb
from .manifest_store import insert_metrics_row, get_connection
from datetime import datetime, timedelta
import pandas as pd
from evidently.report import Report
from evidently.metrics import ColumnDriftMetric
import numpy as np

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
    warnings.warn("Metrics logging is enabled. Ensure this is safe for production use.")
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
        warnings.warn(f"Failed to log metrics: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/metrics/drift-check")
async def drift_check(username: str = Depends(verify_credentials), debug: bool = False):
    conn = get_connection()

    now = datetime.utcnow()
    last_7_days = now - timedelta(days=7)
    prev_30_days_start = last_7_days - timedelta(days=30)

    recent_df = pd.read_sql_query("""
        SELECT * FROM metrics
        WHERE timestamp >= ? AND timestamp < ?
    """, conn, params=(last_7_days.isoformat(), now.isoformat()))

    baseline_df = pd.read_sql_query("""
        SELECT * FROM metrics
        WHERE timestamp >= ? AND timestamp < ?
    """, conn, params=(prev_30_days_start.isoformat(), last_7_days.isoformat()))

    conn.close()

    if baseline_df.empty or recent_df.empty:
        return {"status": "error", "message": "Not enough data"}

    # Only check drift for these columns
    columns_to_check = ["embedding_mean_sim", "embedding_max_sim"]

    # Build report with column-level drift metrics
    metrics = [ColumnDriftMetric(column_name=col) for col in columns_to_check]
    report = Report(metrics=metrics)
    report.run(reference_data=baseline_df, current_data=recent_df)
    result_dict = report.as_dict()

    if debug:
        print(json.dumps(result_dict, indent=2))

    drift_results = {}
    drift_scores = []

    for m in result_dict.get("metrics", []):
        res = m.get("result", {})
        col = res.get("column_name")  # FIX: column_name is in result, not metric
        if col and col in columns_to_check:
            safe_result = {
                "drift_detected": bool(res.get("drift_detected", False)),
                "drift_score": float(res.get("drift_score", 0.0)),
                "stattest_name": str(res.get("stattest_name", "")),
            }
            drift_results[col] = safe_result
            drift_scores.append(safe_result["drift_score"])


    drift_score_avg = float(np.mean(drift_scores)) if drift_scores else None
    drift_score_threshold = 0.3
    retrain_recommended = drift_score_avg is not None and drift_score_avg > drift_score_threshold
    drift_detected = any(v["drift_detected"] for v in drift_results.values())

    return {
        "status": "ok",
        "drift_detected": drift_detected,
        "retrain_recommended": retrain_recommended,
        "drift_score_avg": drift_score_avg,
        "details": drift_results,
        "baseline_count": len(baseline_df),
        "recent_count": len(recent_df),
        "drift_score_threshold": drift_score_threshold
    }