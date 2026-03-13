-- ─────────────────────────────────────────
-- TABLE 1: papers
-- 论文基本信息
-- ─────────────────────────────────────────
CREATE TABLE papers (
    id                  SERIAL PRIMARY KEY,
    pmid                VARCHAR(20) UNIQUE,
    doi                 VARCHAR(100),
    title               TEXT,
    abstract            TEXT,
    journal             VARCHAR(200),
    year                INT,
    authors             TEXT,                  -- JSON数组 ["El Amerany F", "Meddich A"]
    keywords            TEXT,                  -- JSON数组
    pdf_path            VARCHAR(500),
    created_at          TIMESTAMP DEFAULT NOW()
);


-- ─────────────────────────────────────────
-- TABLE 2: experiments
-- 一个实验组一条记录
-- ─────────────────────────────────────────
CREATE TABLE experiments (
    id                  SERIAL PRIMARY KEY,
    paper_id            INT REFERENCES papers(id),

    -- 实验对象
    species             VARCHAR(200),          -- 番茄
    species_ncbi_id     INT,                   -- 4081
    cultivar            VARCHAR(200),          -- Floradade, Candela F1
    plant_part          VARCHAR(100),          -- 叶片 / 果实 / 根 / 全株

    -- 实验设计
    growth_stage        VARCHAR(100),          -- 苗期 / 营养生长期 / 开花期
    growth_medium       VARCHAR(100),          -- 土壤 / 水培 / 琼脂培养基
    duration_days       INT,                   -- 实验时长（天）
    sample_size         INT,                   -- n=8
    experiment_type     VARCHAR(50),           -- pot / field / in_vitro / postharvest

    -- 处理信息
    treatment_substance VARCHAR(200),          -- 壳聚糖
    treatment_mesh_id   VARCHAR(50),           -- MESH:D048271
    treatment_form      VARCHAR(100),          -- 普通壳聚糖 / 纳米颗粒 / Cu-壳聚糖
    application_mode    VARCHAR(100),          -- 叶面喷施 / 根部灌施 / 涂膜 / 浸种
    concentration       FLOAT,                 -- 1.0
    concentration_unit  VARCHAR(50),           -- mg/mL / % / µg/mL / ppm
    frequency           VARCHAR(100),          -- 每两周一次 / 单次
    application_timing  VARCHAR(100),          -- 移栽后25天 / 开花前

    -- 对照组
    control_description VARCHAR(200),          -- 清水处理 / 未处理

    -- 背景条件（多因素实验的额外变量）
    background_conditions TEXT,               -- JSON {"mycorrhiza": "Rhizophagus irregularis", "stress": "Cd 0.8mM"}

    -- 来源
    source_section      VARCHAR(50),           -- abstract / methods / results
    source_table        VARCHAR(50),           -- Table 1 / Figure 3
    extraction_confidence VARCHAR(20),         -- high / medium / low
    notes               TEXT,

    created_at          TIMESTAMP DEFAULT NOW()
);


-- ─────────────────────────────────────────
-- TABLE 3: results
-- 一个指标一条记录，关联experiment
-- ─────────────────────────────────────────
CREATE TABLE results (
    id                  SERIAL PRIMARY KEY,
    experiment_id       INT REFERENCES experiments(id),

    -- 指标
    metric              VARCHAR(200),          -- 地上部生物量 / SPAD值 / 菌根侵染率
    metric_category     VARCHAR(100),          -- growth / physiology / gene_expression
                                               -- postharvest / defense / yield

    -- 结果数值
    value_treatment     FLOAT,                 -- 处理组数值 41.7
    value_control       FLOAT,                 -- 对照组数值 32.1
    unit                VARCHAR(50),           -- g / % / N / mg/L
    change_vs_control   FLOAT,                 -- +30% 存为 30
    direction           VARCHAR(20),           -- increase / decrease / no_change

    -- 统计
    significance        BOOLEAN,               -- 是否显著
    p_value             FLOAT,                 -- 0.05
    std_error           FLOAT,
    test_method         VARCHAR(100),          -- ANOVA / Duncan / t-test

    -- 无数值时的描述
    qualitative_result  TEXT,                  -- "显著上调" / "无显著差异"

    -- 来源
    source_sentence     TEXT,                  -- 原文句子，溯源用
    source_table        VARCHAR(50),           -- Table 2

    created_at          TIMESTAMP DEFAULT NOW()
);


-- ─────────────────────────────────────────
-- TABLE 4: controlled_vocabulary
-- 标准词典，保证名词统一
-- ─────────────────────────────────────────
CREATE TABLE controlled_vocabulary (
    id              SERIAL PRIMARY KEY,
    standard_term   VARCHAR(200) NOT NULL,     -- 标准名 "foliar spray"
    aliases         TEXT,                      -- JSON ["叶面喷施","叶喷","foliar application"]
    category        VARCHAR(100) NOT NULL,     -- 见下方注释
                                               -- application_mode: 叶面喷施/根部灌施/涂膜
                                               -- metric: SPAD值/生物量/菌根侵染率
                                               -- treatment_form: 普通壳聚糖/纳米颗粒
                                               -- growth_stage: 苗期/开花期
                                               -- plant_part: 叶片/根/果实
                                               -- experiment_type: pot/field/postharvest
    external_id     VARCHAR(100),              -- MESH:D048271 / NCBI:4081 (如果有对应标准库)
    external_db     VARCHAR(50),               -- MeSH / NCBI_Taxonomy / NCBI_Gene
    definition      TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cv_category ON controlled_vocabulary(category);


-- ─────────────────────────────────────────
-- 索引
-- ─────────────────────────────────────────
CREATE INDEX idx_experiments_paper    ON experiments(paper_id);
CREATE INDEX idx_experiments_species  ON experiments(species_ncbi_id);
CREATE INDEX idx_experiments_treatment ON experiments(treatment_mesh_id);
CREATE INDEX idx_results_experiment   ON results(experiment_id);
CREATE INDEX idx_results_metric       ON results(metric_category);