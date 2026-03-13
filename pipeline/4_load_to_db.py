"""
DB Loader — Step 4
职责：把normalized数据写入PostgreSQL
输入: data/normalized/*.json
输出: PostgreSQL数据库

依赖: pip install psycopg2-binary
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from db.connection import get_connection


# ─────────────────────────────────────────
# 写入函数
# ─────────────────────────────────────────

def insert_paper(cur, data: dict) -> int:
    """
    插入论文记录，返回paper_id
    已存在（同 title + pdf_path）则返回已有id
    """
    title = data.get("title", "") or ""
    pdf_path = data.get("pdf_path", "") or ""

    # 已存在则直接返回
    cur.execute(
        "SELECT id FROM papers WHERE title = %s AND COALESCE(pdf_path, '') = %s",
        (title, pdf_path),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        "INSERT INTO papers (title, pdf_path) VALUES (%s, %s) RETURNING id",
        (title, pdf_path),
    )
    return cur.fetchone()[0]


def insert_experiment(cur, paper_id: int, exp: dict) -> int:
    """
    插入实验组记录，返回experiment_id
    """
    cur.execute("""
        INSERT INTO experiments (
            paper_id,
            species, cultivar, plant_part,
            growth_stage, growth_medium, duration_days,
            sample_size, experiment_type,
            treatment_substance, treatment_mesh_id,
            treatment_form, application_mode,
            concentration, concentration_unit,
            frequency, application_timing,
            control_description, background_conditions
        ) VALUES (
            %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s
        )
        RETURNING id
    """, (
        paper_id,
        exp.get("species"),
        exp.get("cultivar"),
        exp.get("plant_part"),
        exp.get("growth_stage"),
        exp.get("growth_medium"),
        exp.get("duration_days"),
        exp.get("sample_size"),
        exp.get("experiment_type"),
        exp.get("treatment_substance"),
        exp.get("treatment_mesh_id"),
        exp.get("treatment_form"),
        exp.get("application_mode"),
        exp.get("concentration"),
        exp.get("concentration_unit"),
        exp.get("frequency"),
        exp.get("application_timing"),
        exp.get("control_description"),
        json.dumps(exp.get("background_conditions") or {})
    ))
    return cur.fetchone()[0]


def insert_results(cur, experiment_id: int, results: list):
    """
    批量插入实验结果
    """
    for r in results:
        cur.execute("""
            INSERT INTO results (
                experiment_id,
                metric, metric_category,
                value_treatment, value_control,
                unit, change_vs_control, direction,
                significance, p_value, std_error,
                qualitative_result
            ) VALUES (
                %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s
            )
        """, (
            experiment_id,
            r.get("metric"),
            r.get("metric_category"),
            r.get("value_treatment"),
            r.get("value_control"),
            r.get("unit"),
            r.get("change_vs_control"),
            r.get("direction"),
            r.get("significance"),
            r.get("p_value"),
            r.get("std_error"),
            r.get("qualitative_result")
        ))


# ─────────────────────────────────────────
# 单篇加载（供 API 上传使用）
# ─────────────────────────────────────────

def load_single(data: dict) -> None:
    """
    将单篇 normalized 数据写入数据库
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        paper_id = insert_paper(cur, data)
        for exp in data.get("experiments", []):
            exp_id = insert_experiment(cur, paper_id, exp)
            insert_results(cur, exp_id, exp.get("results", []))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────
# 批量加载
# ─────────────────────────────────────────

def load_batch(normalized_dir: str):
    normalized_dir = Path(normalized_dir)
    files = list(normalized_dir.glob("*.json"))
    print(f"Found {len(files)} normalized files\n")

    conn = get_connection()
    cur = conn.cursor()

    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {path.name}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            paper_id = insert_paper(cur, data)
            print(f"  paper_id: {paper_id}")

            exp_count = 0
            result_count = 0
            for exp in data.get("experiments", []):
                exp_id = insert_experiment(cur, paper_id, exp)
                results = exp.get("results", [])
                insert_results(cur, exp_id, results)
                exp_count += 1
                result_count += len(results)

            conn.commit()
            print(f"  {exp_count} experiments, {result_count} results inserted\n")

        except Exception as e:
            conn.rollback()
            print(f"  ERROR: {e}\n")

    cur.close()
    conn.close()
    print("Done!")


# ─────────────────────────────────────────
# 运行
# ─────────────────────────────────────────

if __name__ == "__main__":
    load_batch("data/normalized/")