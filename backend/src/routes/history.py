from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
from src.db import get_db_connection

router = APIRouter()

@router.get("/api/history")
async def get_history():
    """Fetches the list of past architecture designs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, topic FROM architectures ORDER BY id DESC LIMIT 15;")
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/history/{doc_id}")
async def get_history_document(doc_id: str):
    """Fetches the full markdown for a specific architecture"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT topic, markdown FROM architectures WHERE id=%s;", (doc_id,))
        record = cursor.fetchone()
        cursor.close()
        conn.close()
        if not record: raise HTTPException(status_code=404, detail="Document not found")
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/document/{doc_id}")
async def get_document(doc_id: str):
    """Redundant alias for history fetching, used by generated documents"""
    return await get_history_document(doc_id)