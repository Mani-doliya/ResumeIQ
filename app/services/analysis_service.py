import time
import logging
from typing import Tuple

from app.models.schemas import (
    AnalysisResult, CandidateProfile, SkillGap, DomainPrediction
)
from app.services.resume_parser import resume_parser
from app.services.skill_extractor import skill_extractor
from app.services.matcher import resume_matcher
from app.services.ats_scorer import ats_scorer
from app.services.domain_classifier import domain_classifier

logger = logging.getLogger(__name__)


class AnalysisService:
    def analyze(self, resume_text: str, job_description: str) -> AnalysisResult:
        start = time.perf_counter()

        candidate = resume_parser.parse(resume_text)
        jd_skills = skill_extractor.extract_skills(job_description)
        resume_skills = candidate.extracted_skills

        matched, missing, match_pct = skill_extractor.compute_skill_overlap(
            resume_skills, jd_skills
        )

        similarity = resume_matcher.compute_similarity(resume_text, job_description)
        matched_keywords = resume_matcher.extract_matched_keywords(resume_text, job_description)

        ats = ats_scorer.calculate(
            resume_text, candidate, match_pct, similarity, matched_keywords
        )

        domain_name, domain_conf, top_domains = domain_classifier.classify(
            resume_text, resume_skills
        )

        has_contact = bool(candidate.email or candidate.phone)
        ranking = resume_matcher.rank_candidate(
            similarity, match_pct, candidate.experience_years,
            has_contact, candidate.raw_text_length
        )

        recommendations = ats_scorer.generate_recommendations(ats, missing, candidate)

        priority_gaps = missing[:8]

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        return AnalysisResult(
            candidate=candidate,
            ats_score=ats,
            skill_gap=SkillGap(
                missing_skills=missing,
                matched_skills=matched,
                match_percentage=match_pct,
                priority_gaps=priority_gaps
            ),
            domain=DomainPrediction(
                domain=domain_name,
                confidence=domain_conf,
                top_domains=top_domains
            ),
            similarity_score=similarity,
            ranking_score=ranking,
            matched_keywords=matched_keywords,
            recommendations=recommendations,
            processing_time_ms=elapsed_ms
        )


analysis_service = AnalysisService()