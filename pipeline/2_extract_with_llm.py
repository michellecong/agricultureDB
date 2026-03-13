"""
LLM Extractor — Step 2
职责：用Gemini从论文原始文字中提取结构化实验数据
输入: data/parsed/*.json
输出: data/extracted/*.json

策略：拆分提取，避免 8192 token 输出限制
- 第一次：提取实验框架（不含 results）
- 第二次：针对每个实验组逐一提取 results
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ─────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────

PROMPT_EXPERIMENTS = """You are a scientific data extraction assistant for agricultural research papers.

Extract ALL experimental groups from the paper. Each group = one treatment condition.
Return ONLY a valid JSON object, no markdown, no explanation. Do NOT include "results" field.

{
  "title": "paper title",
  "species": "plant species if stated at paper level",
  "experiments": [
    {
      "group_id": 1,
      "species": "Solanum lycopersicum",
      "cultivar": "if mentioned, else null",
      "plant_part": "leaf / fruit / root / whole plant",
      "growth_stage": "seedling / vegetative / flowering / etc",
      "growth_medium": "soil / hydroponic / agar / etc",
      "duration_days": number or null,
      "sample_size": number or null,
      "experiment_type": "pot / field / in_vitro / postharvest",
      "treatment_substance": "exact name, use 'control' for control group",
      "treatment_form": "nanoparticle / solution / coating / etc or null",
      "application_mode": "foliar spray / root drench / coating / seed soaking / etc or null",
      "concentration": number or null,
      "concentration_unit": "mg/mL / % / µg/mL / mM / ppm / etc or null",
      "frequency": "if mentioned, else null",
      "application_timing": "if mentioned, else null",
      "control_description": "what the control group received",
      "background_conditions": {"key": "value"}
    }
  ]
}

Rules:
- Extract every experimental group separately
- If a paper has control / Cd / CTS-NPs / Cd+CTS-NPs groups, that is 4 experiments
- sample_size: look for "n=X", "X replicates", "X pots", "X plants per treatment", convert "three"→3, "four"→4, etc.
"""

PROMPT_RESULTS = """You are a scientific data extraction assistant for agricultural research papers.

For this specific experiment group:
{group_description}

Extract ALL measured metrics and their values for this group from the paper.
Return ONLY a valid JSON object, no markdown, no explanation.

{{
  "results": [
    {{
      "metric": "exact metric name e.g. shoot dry weight, Fv/Fm, SPAD index, CAT activity",
      "metric_category": "growth / physiology / gene_expression / postharvest / defense / yield",
      "value_treatment": number or null,
      "value_control": number or null,
      "unit": "unit or null",
      "change_vs_control": number or null,
      "direction": "increase / decrease / no_change",
      "significance": true / false / null,
      "p_value": number or null,
      "std_error": number or null,
      "qualitative_result": "brief description if no numeric value, else null"
    }}
  ]
}}

Rules:
- metrics must be specific: "shoot dry weight", "Fv/Fm", "SPAD index", "CAT activity"
- NEVER use broad categories like "plant morphology", "chlorophyll fluorescence" as metric names
- change_vs_control: positive=increase (e.g. +30% → 30), negative=decrease (e.g. -24% → -24)
- If no numeric value, extract qualitative_result (max 10 words)
"""


# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────

def smart_truncate(text: str, max_chars: int = 15000) -> str:
    if len(text) <= max_chars:
        return text

    lower = text.lower()
    results_pos = -1
    for keyword in ["3. results", "results\n", "results and discussion"]:
        pos = lower.find(keyword)
        if pos != -1:
            results_pos = pos
            break

    ref_pos = len(text)
    for keyword in ["references\n", "bibliography\n"]:
        pos = lower.rfind(keyword)
        if pos != -1:
            ref_pos = pos
            break

    if results_pos == -1:
        half = max_chars // 2
        return text[:half] + "\n...\n" + text[ref_pos - half : ref_pos]

    abstract = text[:3000]
    results_section = text[results_pos:ref_pos]
    combined = abstract + "\n...\n" + results_section
    if len(combined) <= max_chars:
        return combined

    remaining = max_chars - len(abstract) - 6
    return abstract + "\n...\n" + results_section[:remaining]


def _call_gemini(prompt: str, max_tokens: int = 8192) -> str:
    """调用 Gemini，返回原始文本"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"max_output_tokens": max_tokens},
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _parse_json(raw: str) -> dict | list:
    """解析 JSON，支持截断修复"""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        for i in range(len(raw) - 1, 0, -1):
            try:
                return json.loads(raw[: i + 1])
            except json.JSONDecodeError:
                continue
        raise ValueError("Cannot parse JSON response")


# ─────────────────────────────────────────
# 提取函数
# ─────────────────────────────────────────

def extract_experiments(parsed: dict) -> dict:
    """
    拆分提取：先提取实验框架，再逐组提取 results
    """
    text = parsed.get("text", "")
    tables = parsed.get("tables", [])

    input_text = text
    if tables:
        input_text += "\n\n=== TABLES ===\n"
        for t in tables:
            input_text += f"\nHeaders: {t['headers']}\n"
            for row in t["rows"]:
                input_text += f"{row}\n"

    input_text = smart_truncate(input_text)

    # Step A: 提取实验框架（不含 results）
    prompt_a = PROMPT_EXPERIMENTS + "\n\nPaper text:\n" + input_text
    raw_a = _call_gemini(prompt_a)
    framework = _parse_json(raw_a)
    time.sleep(1)

    # Step B: 逐组提取 results
    experiments = framework.get("experiments", [])
    for i, exp in enumerate(experiments):
        group_desc = (
            f"treatment={exp.get('treatment_substance', '')}, "
            f"species={exp.get('species', '')}, "
            f"application_mode={exp.get('application_mode', '')}"
        )
        prompt_b = (
            PROMPT_RESULTS.format(group_description=group_desc)
            + "\n\nPaper text:\n"
            + input_text
        )
        raw_b = _call_gemini(prompt_b)
        parsed_b = _parse_json(raw_b)
        exp["results"] = parsed_b.get("results", [])
        time.sleep(1)

    return framework


# ─────────────────────────────────────────
# 单篇处理
# ─────────────────────────────────────────

def process_paper(parsed_path: str, output_path: str):
    with open(parsed_path, "r", encoding="utf-8") as f:
        parsed = json.load(f)

    print(f"  Extracting framework + results (split calls)...")
    result = extract_experiments(parsed)

    result["pdf_path"] = parsed.get("pdf_path", "")
    result["parsed_from"] = parsed_path

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    n = len(result.get("experiments", []))
    print(f"  Extracted {n} experimental groups")
    return result


# ─────────────────────────────────────────
# 批量处理
# ─────────────────────────────────────────

def process_batch(parsed_dir: str, output_dir: str):
    parsed_dir = Path(parsed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = list(parsed_dir.glob("*.json"))
    print(f"Found {len(files)} parsed files\n")

    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {path.name}")
        out_path = output_dir / path.name

        if out_path.exists():
            print(f"  Already extracted, skipping\n")
            continue

        try:
            process_paper(str(path), str(out_path))
            print(f"  Saved: {out_path}\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")

        time.sleep(1)


# ─────────────────────────────────────────
# 运行
# ─────────────────────────────────────────

if __name__ == "__main__":
    process_batch("data/parsed/", "data/extracted/")
