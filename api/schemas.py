from pydantic import BaseModel
from typing import Optional


class ResultOut(BaseModel):
    id: int
    metric: Optional[str]
    metric_category: Optional[str]
    value_treatment: Optional[float]
    value_control: Optional[float]
    unit: Optional[str]
    change_vs_control: Optional[float]
    direction: Optional[str]
    significance: Optional[bool]
    qualitative_result: Optional[str]


class ExperimentOut(BaseModel):
    id: int
    paper_id: int
    species: Optional[str]
    treatment_substance: Optional[str]
    treatment_form: Optional[str]
    application_mode: Optional[str]
    concentration: Optional[float]
    concentration_unit: Optional[str]
    experiment_type: Optional[str]
    growth_medium: Optional[str]
    duration_days: Optional[int]
    sample_size: Optional[int]
    results: list[ResultOut] = []


class PaperOut(BaseModel):
    id: int
    title: Optional[str]
    doi: Optional[str]
    journal: Optional[str]
    year: Optional[int]
    experiment_count: Optional[int] = 0