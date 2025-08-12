import sqlite3
from pathlib import Path
from .config import SQLITE_DB_PATH

def get_connection():
    Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS manifest (
        manifest_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT,
        chunk_id TEXT,
        chunk_index INTEGER,
        index_version TEXT,
        created_at TEXT,
        metadata_json TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS index_versions (
        version TEXT PRIMARY KEY,
        created_at TEXT,
        total_chunks INTEGER,
        is_active INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        session_id TEXT,
        query_id TEXT,
        user_query TEXT,
        top_doc_ids TEXT,
        top_doc_scores TEXT,
        embedding_mean_sim REAL,
        embedding_max_sim REAL,
        model_answer TEXT,
        answer_length_tokens INTEGER,
        hallucination_flag INTEGER,
        latency_ms INTEGER,
        source_index_version TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_manifest_rows(rows):
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
    INSERT INTO manifest (doc_id, chunk_id, chunk_index, index_version, created_at, metadata_json)
    VALUES (?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    conn.close()

def insert_index_version(version, created_at, total_chunks, is_active=1):
    conn = get_connection()
    cur = conn.cursor()
    # deactivate others if active
    if is_active:
        cur.execute("UPDATE index_versions SET is_active = 0")
    cur.execute("""
    INSERT OR REPLACE INTO index_versions (version, created_at, total_chunks, is_active)
    VALUES (?, ?, ?, ?)
    """, (version, created_at, total_chunks, is_active))
    conn.commit()
    conn.close()

def insert_metrics_row(row):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO metrics (
        timestamp, session_id, query_id, user_query, top_doc_ids, top_doc_scores,
        embedding_mean_sim, embedding_max_sim, model_answer, answer_length_tokens,
        hallucination_flag, latency_ms, source_index_version
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)
    conn.commit()
    conn.close()

def get_active_version():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT version FROM index_versions WHERE is_active=1 LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
