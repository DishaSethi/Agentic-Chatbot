from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from google import genai

from src.schemas.models import EvaluateRequest
from src.db import get_db_connection
from src.graph.eval_graph import eval_app
from langsmith import traceable
router = APIRouter()
gemini_client = genai.Client()


@traceable(name="NeonDB Hybrid Search", run_type="retriever")
def retrieve_architecture_rules(user_architecture: str, query_embedding: list):
    """Runs the Hybrid Search and is tracked by LangSmith"""
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""WITH vector_search AS (
    SELECT category, content, source_url, RANK() OVER(ORDER BY embedding <=> %s:: vector) AS dense_rank FROM best_practices LIMIT 10),
    keyword_search AS (
    SELECT category, content, source_url , RANK() OVER(ORDER BY ts_rank_cd(to_tsvector('english', content), websearch_to_tsquery('english',%s))DESC) AS sparse_rank
    FROM best_practices WHERE to_tsvector('english', content) @@ websearch_to_tsquery('english',%s) LIMIT 10)
    SELECT COALESCE(v.category, k.category) AS category, COALESCE(v.content, k.content) AS content, COALESCE(v.source_url, k.source_url) AS source_url,
    (COALESCE(1.0/(v.dense_rank+60),0.0)+COALESCE(1.0/(k.sparse_rank+60),0.0)) AS rrf_score
    FROM vector_search v FULL OUTER JOIN keyword_search k ON v.content=k.content ORDER BY rrf_score DESC LIMIT 3;""",
    (query_embedding, user_architecture, user_architecture))

    retrieved_docs = cursor.fetchall()
    cursor.close()
    conn.close()

    return retrieved_docs



@router.post("/api/evaluate")
async def evaluate_architecture(req: EvaluateRequest):
    try:
        embed_response = gemini_client.models.embed_content(
            model="gemini-embedding-001", contents=req.user_architecture
        )
        query_embedding = embed_response.embeddings[0].values


        retrieved_docs = retrieve_architecture_rules(req.user_architecture,query_embedding)



        print("\n" + "="*50 + "\n🔍 RAG AUDIT: TOP 3 MATCHES FROM NEON DB\n" + "="*50)
        if not retrieved_docs: print("⚠️ WARNING: DB returned ZERO results.")

        citations_payload = []
        if retrieved_docs:
            context = ""
            for i, doc in enumerate(retrieved_docs):
                score=f"{doc.get('rrf_score',0):.4f}"
                print(f"\n--- MATCH {i+1} [{doc['category']}] (Score:{score}) ---\nCONTENT: {doc['content'][:150]}")

                category_id = doc['category']
                context += f"[{category_id}] {doc['content']}\n\n"
                citations_payload.append({"id": category_id, "title": category_id, "content": doc['content'], "url":doc.get('source_url','#')})
        else:
            context = "General Distributed Systems and Cloud Architecture Best Practices."

        print("\n" + "="*50 + "\n🚀 STARTING LANGGRAPH SELF-RAG LOOP\n" + "="*50)

        final_state = eval_app.invoke({
            "user_architecture": req.user_architecture, "context": context,
            "draft_scorecard": "", "is_hallucinated": False, "iterations": 0
        })

        return {"evaluation_scorecard": final_state["draft_scorecard"], "matched_rules_count": len(retrieved_docs), "citations": citations_payload}

    except Exception as e:
        print(f"RAG Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))