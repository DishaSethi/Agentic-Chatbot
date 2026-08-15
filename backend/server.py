import os
import uuid
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv       # <--- IMPORT DOTENV
import psycopg2                      # <--- IMPORT POSTGRES DRIVER
from psycopg2.extras import RealDictCursor # <--- Returns DB rows as Python dictionaries
from pgvector.psycopg2 import register_vector
from src.graph.main_graph import app as graph_engine
from google import genai
from google.genai import types



# --- DATABASE CONFIGURATION ---
# Load variables from the .env file
load_dotenv()
gemini_client=genai.Client()



# Get the Neon DB URL from the environment
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file!")

app = FastAPI(title="AI Architect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    user_architecture: str

class PlanRequest(BaseModel):
    topic: str

class ApproveRequest(BaseModel):
    thread_id: str
    topic: str

@app.post("/api/plan")
async def generate_plan(req: PlanRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "topic": req.topic,
        "as_of": date.today().isoformat(),
        "research_loop_count": 0
    }

    for chunk in graph_engine.stream(initial_state, config=config):
        pass

    current_state = graph_engine.get_state(config)
    plan = current_state.values.get("plan")

    if not plan:
        raise HTTPException(status_code=500, detail="Planning failed.")

    return {
        "thread_id": thread_id,
        "system_title": plan.system_title,
        "tasks": [{"title": t.title, "goal": t.goal, "bullets": t.bullets} for t in plan.tasks]
    }

@app.post("/api/generate")
async def generate_document(req: ApproveRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    for chunk in graph_engine.stream(None, config=config):
        pass

    final_state = graph_engine.get_state(config)
    final_md = final_state.values.get("merged_md")


    doc_id = None
    try:
        # Open connection to Neon
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Execute the INSERT query and RETURNING id gets the auto-generated UUID back
        cursor.execute(
            "INSERT INTO architectures (topic, markdown) VALUES (%s, %s) RETURNING id;",
            (req.topic, final_md)
        )

        # Fetch the newly created ID
        inserted_row = cursor.fetchone()
        if inserted_row:
            doc_id = inserted_row["id"]

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Neon Database error: {e}")

    return {
        "markdown": final_md,
        "doc_id": doc_id
    }

@app.get("/api/document/{doc_id}")
async def get_document(doc_id: str):
    try:
        # Open connection to Neon
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch the document by ID
        cursor.execute("SELECT * FROM architectures WHERE id = %s;", (doc_id,))
        document = cursor.fetchone()

        cursor.close()
        conn.close()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate")
async def evaluate_architecture(req: EvaluateRequest):
    """
    Evaluates an architecture document against best practices stored in Neon DB
    using Gemini text-embedding-004 and gemini-2.5-flash.
    """
    try:
        # 1. Generate 768-dimensional vector embedding using Gemini
        embed_response = gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=req.user_architecture,
        )
        query_embedding = embed_response.embeddings[0].values

        # 2. Query Neon DB for the top 3 semantically closest best practices
        conn = psycopg2.connect(DATABASE_URL)
        register_vector(conn)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT category, content
            FROM best_practices
            ORDER BY embedding <=> %s::vector
            LIMIT 3;
        """, (query_embedding,))

        retrieved_docs = cursor.fetchall()
        cursor.close()
        conn.close()

        # 3. Build context from retrieved rules
        if retrieved_docs:
            context = "\n\n".join([f"[{doc['category']}] {doc['content']}" for doc in retrieved_docs])
        else:
            context = "General Distributed Systems and Cloud Architecture Best Practices."

        system_prompt = f"""
You are a Principal Cloud Systems Architect evaluating a system design architecture.
Compare the user's architecture against these industry best practices retrieved from our knowledge base:

<best_practices>
{context}
</best_practices>

Generate a comprehensive Markdown evaluation report structured as follows:
## 📊 Architecture Evaluation Scorecard
### 1. Strengths & Good Alignment
### 2. Critical Bottlenecks & Security Gaps
### 3. Recommendations & Mitigations
"""

        # 4. Generate the evaluation report using Gemini
        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=f"{system_prompt}\n\nUser Architecture:\n{req.user_architecture}"
        )

        return {
            "evaluation_scorecard": response.text,
            "matched_rules_count": len(retrieved_docs)
        }

    except Exception as e:
        print(f"RAG Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)