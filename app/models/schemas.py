from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SkillMatch(BaseModel):
    skill: str
    found_in_resume: bool
    relevance_score: float = 0.0


class SkillGap(BaseModel):
    missing_skills: List[str]
    matched_skills: List[str]
    match_percentage: float
    priority_gaps: List[str] = []


class ATSScoreBreakdown(BaseModel):
    overall_score: float
    keyword_match: float
    skills_coverage: float
    experience_relevance: float
    formatting_score: float
    section_completeness: float


class DomainPrediction(BaseModel):
    domain: str
    confidence: float
    top_domains: List[Dict[str, Any]] = []


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    experience_years: Optional[float] = None
    education: List[str] = []
    extracted_skills: List[str] = []
    raw_text_length: int = 0


class AnalysisResult(BaseModel):
    candidate: CandidateProfile
    ats_score: ATSScoreBreakdown
    skill_gap: SkillGap
    domain: DomainPrediction
    similarity_score: float
    ranking_score: float
    matched_keywords: List[str]
    recommendations: List[str]
    processing_time_ms: float


class JobDescriptionInput(BaseModel):
    text: str = Field(..., min_length=50, max_length=15000)
    title: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    python_version: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class EvaluationMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    support: int = 0