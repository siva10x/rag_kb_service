import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
from app.manifest_store import get_connection
from docx import Document

# Load KB docx
doc = Document("trendora_knowledge_base_with_products.docx")

# Extract product info
product_info = []
current_product = None
for para in doc.paragraphs:
    text = para.text.strip()
    if not text:
        continue
    if (
        text.istitle()
        or text.isupper()
        or "Trendora" in text
        or "Pro" in text
        or "Smartwatch" in text
        or "Buds" in text
        or "Phone" in text
    ) and len(text.split()) <= 6:
        current_product = text
    else:
        if current_product:
            product_info.append((current_product, text))
            current_product = None

# Generate Q&A pairs
qa_pairs = []
for name, desc in product_info:
    qa_pairs.append((f"Tell me about {name}.", desc))
    qa_pairs.append((f"What are the key features of {name}?", "Key features include: " + desc.split('.')[0] + "."))
    qa_pairs.append((f"Is {name} available for purchase?", f"Yes, {name} is available on Trendora's website."))

print(f"Loaded {len(qa_pairs)} Q&A pairs from KB.")

# Insert synthetic data
conn = get_connection()
cur = conn.cursor()

# Clear old data first
cur.execute("DELETE FROM metrics")
conn.commit()
print("🗑️ Cleared existing metrics table.")

now = datetime.utcnow()

for days_ago in range(40, -1, -1):  # 40 days ago to today
    ts = (now - timedelta(days=days_ago)).isoformat()
    query, answer = random.choice(qa_pairs)

    # Simulate drift in last 7 days
    if days_ago > 7:
        mean_sim = round(random.uniform(0.88, 0.95), 16)
    else:
        mean_sim = round(random.uniform(0.70, 0.80), 16)

    max_sim = round(min(mean_sim + random.uniform(10.01, 0.05), 1.0), 16)

    # Randomized retrieved doc IDs and scores
    doc_ids = [f"trendora-doc-{i}" for i in range(1, 46)]  # simulate 45 possible chunks
    retrieved_ids = ",".join(random.sample(doc_ids, k=3))
    scores = ",".join(str(round(random.uniform(0.1, 1.0), 3)) for _ in range(3))

    cur.execute("""
        INSERT INTO metrics (
            timestamp, session_id, query_id, user_query, top_doc_ids, top_doc_scores,
            embedding_mean_sim, embedding_max_sim, model_answer, answer_length_tokens,
            hallucination_flag, latency_ms, source_index_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts,
        f"sess-{days_ago}",
        f"q-{days_ago}",
        query,
        retrieved_ids,      # randomized doc IDs
        scores,             # randomized doc scores
        mean_sim,
        max_sim,
        answer,
        len(answer.split()),
        1 if random.random() < 0.05 else 0,
        random.randint(200, 500),
        "index-demo"
    ))

conn.commit()
conn.close()
print("✅ Synthetic metrics data inserted.")
