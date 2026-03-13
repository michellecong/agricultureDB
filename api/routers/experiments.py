from fastapi import APIRouter, Query
from typing import Optional
from db.connection import get_connection

router = APIRouter()


@router.get("/")
def search_experiments(
    species: Optional[str] = Query(None),
    treatment: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    paper_id: Optional[int] = Query(None),
):
    """
    按物种/处理/指标/方向筛选实验数据
    """
    conn = get_connection()
    cur = conn.cursor()

    conditions = []
    params = []

    if paper_id:
        conditions.append("e.paper_id = %s")
        params.append(paper_id)
    if species:
        conditions.append("LOWER(e.species) LIKE %s")
        params.append(f"%{species.lower()}%")
    if treatment:
        conditions.append("LOWER(e.treatment_substance) LIKE %s")
        params.append(f"%{treatment.lower()}%")
    if metric:
        conditions.append("LOWER(r.metric) LIKE %s")
        params.append(f"%{metric.lower()}%")
    if direction:
        conditions.append("r.direction = %s")
        params.append(direction)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    cur.execute(f"""
        SELECT
            e.id, e.species, e.treatment_substance,
            e.application_mode, e.concentration, e.concentration_unit,
            e.experiment_type,
            r.metric, r.metric_category,
            r.value_treatment, r.value_control,
            r.unit, r.change_vs_control, r.direction,
            r.significance, r.qualitative_result,
            p.title, p.id as paper_id
        FROM experiments e
        JOIN papers p ON p.id = e.paper_id
        LEFT JOIN results r ON r.experiment_id = e.id
        {where}
        ORDER BY e.id, r.metric
    """, params)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "experiment_id": r[0],
            "species": r[1],
            "treatment": r[2],
            "application_mode": r[3],
            "concentration": r[4],
            "concentration_unit": r[5],
            "experiment_type": r[6],
            "metric": r[7],
            "metric_category": r[8],
            "value_treatment": r[9],
            "value_control": r[10],
            "unit": r[11],
            "change_vs_control": r[12],
            "direction": r[13],
            "significance": r[14],
            "qualitative_result": r[15],
            "paper_title": r[16],
            "paper_id": r[17],
        }
        for r in rows
    ]


@router.patch("/{experiment_id}/results/{result_id}")
def update_result(experiment_id: int, result_id: int, data: dict):
    """
    编辑单条结果
    """
    allowed = {"metric", "value_treatment", "value_control",
                "change_vs_control", "direction", "qualitative_result"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return {"status": "nothing to update"}

    conn = get_connection()
    cur = conn.cursor()
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    params = list(updates.values()) + [result_id, experiment_id]
    cur.execute(
        f"UPDATE results SET {set_clause} WHERE id = %s AND experiment_id = %s",
        params
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "updated"}