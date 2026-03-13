"""
PDF Parser — Step 1
职责：从PDF提取干净的原始文字 + 表格
不做章节识别，交给LLM处理

依赖:
    pip install pymupdf pdfplumber
"""

import json
import re
import fitz
import pdfplumber
from pathlib import Path


# ─────────────────────────────────────────
# PyMuPDF: 提取原始文字
# ─────────────────────────────────────────

def extract_text(pdf_path: str) -> str:
    """
    提取PDF全文，清洗噪音，返回干净的纯文本
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page in doc:
        # 按阅读顺序提取文字块
        blocks = page.get_text("blocks")  # [(x0,y0,x1,y1,text,block_no,block_type)]
        # 只要文字块，按垂直位置排序
        text_blocks = sorted(
            [b[4] for b in blocks if b[6] == 0],
            key=lambda x: x
        )
        page_text = " ".join(text_blocks)
        pages.append(page_text)

    full_text = "\n\n".join(pages)

    # 清洗
    full_text = re.sub(r'\s+', ' ', full_text)           # 多余空白
    full_text = re.sub(r'\[\d+[\d,\-\s]*\]', '', full_text)  # 引用标记 [1] [2,3] [1-5]
    full_text = re.sub(r'\b\d{1,2} of \d{1,2}\b', '', full_text)  # 页码 "3 of 14"
    full_text = full_text.strip()

    doc.close()
    return full_text


# ─────────────────────────────────────────
# pdfplumber: 提取表格
# ─────────────────────────────────────────

def extract_tables(pdf_path: str) -> list:
    """
    提取PDF中所有表格，返回结构化列表
    """
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            for raw_table in page.extract_tables() or []:
                if not raw_table:
                    continue

                cleaned = [
                    [cell.strip() if isinstance(cell, str) else "" for cell in row]
                    for row in raw_table
                ]

                headers = cleaned[0]
                rows = [
                    dict(zip(headers, row))
                    for row in cleaned[1:]
                    if any(cell for cell in row)
                ]

                if rows:
                    tables.append({
                        "page": page_num,
                        "headers": headers,
                        "rows": rows
                    })

    return tables


# ─────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────

def parse_pdf(pdf_path: str) -> dict:
    """
    解析单篇PDF，输出原始文字 + 表格
    """
    print(f"Parsing: {pdf_path}")

    try:
        text = extract_text(pdf_path)
        print(f"  Text: {len(text)} chars")
    except Exception as e:
        print(f"  Text extraction failed: {e}")
        text = ""

    try:
        tables = extract_tables(pdf_path)
        print(f"  Tables: {len(tables)} found")
    except Exception as e:
        print(f"  Table extraction failed: {e}")
        tables = []

    return {
        "pdf_path": pdf_path,
        "text": text,
        "tables": tables,
    }


# ─────────────────────────────────────────
# 批量处理
# ─────────────────────────────────────────

def parse_batch(pdf_dir: str, output_dir: str):
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = list(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs\n")

    for i, pdf_path in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {pdf_path.name}")
        out_path = output_dir / f"{pdf_path.stem}.json"

        if out_path.exists():
            print(f"  Already processed, skipping\n")
            continue

        try:
            result = parse_pdf(str(pdf_path))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  Saved: {out_path}\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")


# ─────────────────────────────────────────
# 运行
# ─────────────────────────────────────────

if __name__ == "__main__":
    parse_batch("data/pdfs/", "data/parsed/")