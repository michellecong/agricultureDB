"""
Normalizer — Step 3
职责：对提取结果进行词汇归一化
输入: data/extracted/*.json
输出: data/normalized/*.json + review/pending_vocab.json

依赖: pip install requests
"""

import json
import re
import requests
from pathlib import Path


# ─────────────────────────────────────────
# 初始受控词典
# ─────────────────────────────────────────

CONTROLLED_VOCABULARY = {

    # ── 处理物质 (treatment_substance) ──
    "treatment": {
        "chitosan": {
            "standard_term": "chitosan",
            "aliases": ["Chitosan", "CTS", "Ch", "chitosan solution"],
            "external_id": "MESH:D048271",
            "external_db": "MeSH"
        },
        "chitosan nanoparticles": {
            "standard_term": "chitosan nanoparticles",
            "aliases": ["CTS-NPs", "chitosan NPs", "Chitosan-derived nanoparticles",
                       "ChNPs", "nano-chitosan", "chitosan nanoparticle"],
            "external_id": "MESH:D048271",
            "external_db": "MeSH"
        },
        "cu-chitosan nanoparticles": {
            "standard_term": "cu-chitosan nanoparticles",
            "aliases": ["Cu-chitosan NPs", "Cu-CTS-NPs", "copper-chitosan nanoparticles"],
            "external_id": None,
            "external_db": None
        },
        "cadmium": {
            "standard_term": "cadmium",
            "aliases": ["Cd", "CdCl2", "cadmium chloride"],
            "external_id": "MESH:D002104",
            "external_db": "MeSH"
        },
        "iron oxide nanoparticles": {
            "standard_term": "iron oxide nanoparticles",
            "aliases": ["NPs-Fe2O3", "Fe2O3 NPs", "iron oxide NPs"],
            "external_id": None,
            "external_db": None
        },
        "arbuscular mycorrhizal fungi": {
            "standard_term": "arbuscular mycorrhizal fungi",
            "aliases": ["AMF", "Rhizophagus irregularis", "arbuscular mycorrhizal fungi"],
            "external_id": "MESH:D020107",
            "external_db": "MeSH"
        },
        "control": {
            "standard_term": "control",
            "aliases": ["control", "none", "water", "untreated"],
            "external_id": None,
            "external_db": None
        },
    },

    # ── 施用方式 (application_mode) ──
    "application_mode": {
        "foliar spray": {
            "standard_term": "foliar spray",
            "aliases": ["foliar application", "foliar treatment", "leaf spray",
                       "foliar fertigation", "spraying leaves", "叶面喷施"]
        },
        "root drench": {
            "standard_term": "root drench",
            "aliases": ["soil drench", "root treatment", "soil drenching",
                       "root application", "根部灌施"]
        },
        "coating": {
            "standard_term": "coating",
            "aliases": ["fruit coating", "edible coating", "surface coating", "涂膜"]
        },
        "seed soaking": {
            "standard_term": "seed soaking",
            "aliases": ["seed treatment", "seed priming", "浸种"]
        },
    },

    # ── 测量指标 (metric) ──
    "metric": {
        "shoot dry weight": {
            "standard_term": "shoot dry weight",
            "aliases": ["shoot biomass", "shoot fresh weight", "aerial biomass",
                       "aboveground biomass", "shoot DW"]
        },
        "root dry weight": {
            "standard_term": "root dry weight",
            "aliases": ["root biomass", "root fresh weight", "root DW"]
        },
        "SPAD index": {
            "standard_term": "SPAD index",
            "aliases": ["SPAD", "chlorophyll content", "SPAD value",
                       "chlorophyll index", "SPAD chlorophyll"]
        },
        "net photosynthetic rate": {
            "standard_term": "net photosynthetic rate",
            "aliases": ["PN", "photosynthetic rate", "photosynthesis rate",
                       "net photosynthesis", "A"]
        },
        "stomatal conductance": {
            "standard_term": "stomatal conductance",
            "aliases": ["gs", "stomatal conductance (gs)"]
        },
        "transpiration rate": {
            "standard_term": "transpiration rate",
            "aliases": ["E", "transpiration"]
        },
        "internal CO2 concentration": {
            "standard_term": "internal CO2 concentration",
            "aliases": ["Ci", "intercellular CO2", "internal CO2"]
        },
        "Fv/Fm": {
            "standard_term": "Fv/Fm",
            "aliases": ["Fv/Fm ratio", "maximum quantum yield", "photosystem efficiency"]
        },
        "ΦPSII": {
            "standard_term": "ΦPSII",
            "aliases": ["PSII quantum yield", "ΦPS II", "Phi PSII"]
        },
        "qP": {
            "standard_term": "qP",
            "aliases": ["photochemical quenching", "qp"]
        },
        "NPQ": {
            "standard_term": "NPQ",
            "aliases": ["non-photochemical quenching"]
        },
        "mycorrhization rate": {
            "standard_term": "mycorrhization rate",
            "aliases": ["mycorrhization rates", "mycorrhizal colonization",
                       "AM colonization", "mycorrhization"]
        },
        "flower number": {
            "standard_term": "flower number",
            "aliases": ["flower count", "number of flowers", "flowering"]
        },
        "MDA content": {
            "standard_term": "MDA content",
            "aliases": ["malondialdehyde", "MDA", "lipid peroxidation"]
        },
        "H2O2 content": {
            "standard_term": "H2O2 content",
            "aliases": ["hydrogen peroxide", "H2O2"]
        },
        "CAT activity": {
            "standard_term": "CAT activity",
            "aliases": ["catalase activity", "CAT"]
        },
        "POX activity": {
            "standard_term": "POX activity",
            "aliases": ["peroxidase activity", "POX", "POD activity"]
        },
        "SOD activity": {
            "standard_term": "SOD activity",
            "aliases": ["superoxide dismutase activity", "SOD"]
        },
        "GSH content": {
            "standard_term": "GSH content",
            "aliases": ["GSH", "glutathione", "reduced glutathione"]
        },
        "AsA content": {
            "standard_term": "AsA content",
            "aliases": ["AsA", "ascorbic acid", "ascorbate"]
        },
        "protein content": {
            "standard_term": "protein content",
            "aliases": ["leaf protein content", "total protein", "protein"]
        },
        "proline content": {
            "standard_term": "proline content",
            "aliases": ["leaf proline content", "proline"]
        },
        "antioxidant activity": {
            "standard_term": "antioxidant activity",
            "aliases": ["TEAC activity", "CUPRAC activity", "DPPH activity",
                       "total antioxidant capacity"]
        },
    },

    # ── 实验类型 (experiment_type) ──
    "experiment_type": {
        "pot": {"standard_term": "pot", "aliases": ["pot experiment", "greenhouse pot"]},
        "field": {"standard_term": "field", "aliases": ["field experiment", "field trial"]},
        "in_vitro": {"standard_term": "in_vitro", "aliases": ["in vitro", "lab"]},
        "postharvest": {"standard_term": "postharvest", "aliases": ["post-harvest", "storage"]},
    }
}


# ─────────────────────────────────────────
# 归一化函数
# ─────────────────────────────────────────

def build_alias_map(category: str) -> dict:
    """
    把词典展开成 alias→standard_term 的查找表
    """
    alias_map = {}
    for standard_term, entry in CONTROLLED_VOCABULARY[category].items():
        # standard_term本身也加进去
        alias_map[standard_term.lower()] = standard_term
        for alias in entry.get("aliases", []):
            alias_map[alias.lower()] = standard_term
    return alias_map


# 预构建查找表
TREATMENT_MAP = build_alias_map("treatment")
MODE_MAP = build_alias_map("application_mode")
METRIC_MAP = build_alias_map("metric")
TYPE_MAP = build_alias_map("experiment_type")


def normalize_term(term: str, alias_map: dict, pending: list, category: str) -> str:
    """
    归一化单个词，找不到则加入待审核队列
    """
    if not term or term.lower() in ("none", "null"):
        return term

    # 精确匹配
    key = term.lower().strip()
    if key in alias_map:
        return alias_map[key]

    # 模糊匹配：检查是否包含某个alias
    for alias, standard in alias_map.items():
        if alias in key or key in alias:
            return standard

    # 找不到，加入待审核
    pending.append({"term": term, "category": category})
    return term  # 原样保留，等人工审核


def get_external_id(standard_term: str, category: str) -> tuple:
    """
    获取标准术语的外部数据库ID
    """
    vocab = CONTROLLED_VOCABULARY.get(category, {})
    entry = vocab.get(standard_term, {})
    return entry.get("external_id"), entry.get("external_db")


# ─────────────────────────────────────────
# PubTator归一化（物种和化学物）
# ─────────────────────────────────────────

def query_pubtator_species(name: str) -> dict:
    """
    通过NCBI Taxonomy查询物种ID
    """
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "taxonomy", "term": name, "retmode": "json", "retmax": 1}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        if ids:
            return {"ncbi_taxonomy_id": ids[0], "source": "ncbi_taxonomy"}
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────
# 主归一化流程
# ─────────────────────────────────────────

def normalize_paper(extracted: dict) -> dict:
    """
    对单篇论文的提取结果进行归一化
    """
    pending = []  # 待审核词汇
    normalized = dict(extracted)

    for exp in normalized.get("experiments", []):

        # 归一化treatment
        exp["treatment_substance"] = normalize_term(
            exp.get("treatment_substance", ""),
            TREATMENT_MAP, pending, "treatment"
        )
        # 补充外部ID
        ext_id, ext_db = get_external_id(exp["treatment_substance"], "treatment")
        exp["treatment_mesh_id"] = ext_id
        exp["treatment_db"] = ext_db

        # 归一化application_mode
        exp["application_mode"] = normalize_term(
            exp.get("application_mode", ""),
            MODE_MAP, pending, "application_mode"
        )

        # 归一化experiment_type
        exp["experiment_type"] = normalize_term(
            exp.get("experiment_type", ""),
            TYPE_MAP, pending, "experiment_type"
        )

        # 归一化每个result的metric
        for result in exp.get("results", []):
            result["metric"] = normalize_term(
                result.get("metric", ""),
                METRIC_MAP, pending, "metric"
            )

    normalized["_pending_vocab"] = pending
    return normalized


# ─────────────────────────────────────────
# 批量处理
# ─────────────────────────────────────────

def normalize_batch(extracted_dir: str, output_dir: str, pending_path: str):
    extracted_dir = Path(extracted_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_pending = []
    files = list(extracted_dir.glob("*.json"))
    print(f"Found {len(files)} extracted files\n")

    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {path.name}")
        out_path = output_dir / path.name

        with open(path, "r", encoding="utf-8") as f:
            extracted = json.load(f)

        normalized = normalize_paper(extracted)

        # 收集待审核词
        pending = normalized.pop("_pending_vocab", [])
        all_pending.extend(pending)
        if pending:
            print(f"  Pending review: {[p['term'] for p in pending]}")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {out_path}")

    # 保存待审核词汇
    Path(pending_path).parent.mkdir(exist_ok=True)

    # 去重
    seen = set()
    unique_pending = []
    for p in all_pending:
        key = f"{p['category']}:{p['term']}"
        if key not in seen:
            seen.add(key)
            unique_pending.append(p)

    with open(pending_path, "w", encoding="utf-8") as f:
        json.dump(unique_pending, f, ensure_ascii=False, indent=2)

    print(f"\nPending vocab saved: {pending_path} ({len(unique_pending)} terms)")


# ─────────────────────────────────────────
# 运行
# ─────────────────────────────────────────

if __name__ == "__main__":
    normalize_batch(
        "data/extracted/",
        "data/normalized/",
        "review/pending_vocab.json"
    )