from fastapi import APIRouter, HTTPException
from api.schemas import PaperOut
from db.connection import get_connection

router = APIRouter()


@router.get("/", response_model=list[PaperOut])
def list_papers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.title, p.doi, p.journal, p.year,
               COUNT(e.id) as experiment_count
        FROM papers p
        LEFT JOIN experiments e ON e.paper_id = p.id
        GROUP BY p.id
        ORDER BY p.id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        PaperOut(id=r[0], title=r[1], doi=r[2],
                 journal=r[3], year=r[4], experiment_count=r[5])
        for r in rows
    ]


@router.get("/{paper_id}")
def get_paper(paper_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM papers WHERE id = %s", (paper_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"id": row[0], "title": row[2], "doi": row[3]}