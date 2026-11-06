import re
from typing import List, Optional
import logging

from app.models.schemas import ATSScoreBreakdown, CandidateProfile

logger = logging.getLogger(__name__)


class ATSScorer:
    IMPORTANT_SECTIONS = [
        "experience", "education", "skills", "summary", "projects"
    ]

    def calculate(
        self,
        resume_text: str,
        candidate: CandidateProfile,
        skill_match_pct: float,
        similarity_score: float,
        matched_keywords: List[str]
    ) -> ATSScoreBreakdown:
        keyword_score = min(similarity_score, 100.0)
        skills_score = min(skill_match_pct, 100.0)
        experience_score = self._score_experience(candidate, resume_text)
        formatting_score = self._score_formatting(resume_text)
        section_score = self._score_sections(resume_text)

        overall = (
            0.30 * keyword_score +
            0.30 * skills_score +
            0.15 * experience_score +
            0.15 * formatting_score +
            0.10 * section_score
        )
        overall = round(min(max(overall, 0), 100), 2)

        return ATSScoreBreakdown(
            overall_score=overall,
            keyword_match=round(keyword_score, 2),
            skills_coverage=round(skills_score, 2),
            experience_relevance=round(experience_score, 2),
            formatting_score=round(formatting_score, 2),
            section_completeness=round(section_score, 2)
        )

    def _score_experience(self, candidate: CandidateProfile, text: str) -> float:
        score = 40.0
        if candidate.experience_years is not None:
            if candidate.experience_years >= 5:
                score += 40
            elif candidate.experience_years >= 2:
                score += 25
            else:
                score += 10
        if re.search(r'\b(led|managed|architected|designed|implemented|optimized)\b', text.lower()):
            score += 20
        return min(score, 100.0)

    def _score_formatting(self, text: str) -> float:
        score = 50.0
        lines = text.split('\n')
        non_empty = [l for l in lines if l.strip()]
        if len(non_empty) > 20:
            score += 15
        if len(text) > 800:
            score += 15
        if len(text) > 2000:
            score += 10
        has_bullets = bool(re.search(r'[\•\-\*]\s+\w', text))
        if has_bullets:
            score += 10
        return min(score, 100.0)

    def _score_sections(self, text: str) -> float:
        text_lower = text.lower()
        found = 0
        for section in self.IMPORTANT_SECTIONS:
            if section in text_lower:
                found += 1
        return (found / len(self.IMPORTANT_SECTIONS)) * 100

    def generate_recommendations(
        self,
        ats: ATSScoreBreakdown,
        missing_skills: List[str],
        candidate: CandidateProfile
    ) -> List[str]:
        recs = []
        if ats.overall_score < 60:
            recs.append("Overall ATS score is low. Focus on aligning resume keywords with the job description.")
        if ats.keyword_match < 50:
            recs.append("Low keyword match. Incorporate more relevant terms from the job description naturally.")
        if ats.skills_coverage < 50:
            recs.append(f"Skills coverage is limited. Consider adding or highlighting: {', '.join(missing_skills[:5])}")
        if not candidate.email:
            recs.append("Add a professional email address for better contact completeness.")
        if candidate.experience_years is None:
            recs.append("Explicitly state years of experience if applicable.")
        if ats.section_completeness < 60:
            recs.append("Ensure standard sections (Summary, Experience, Education, Skills) are clearly present.")
        if ats.formatting_score < 60:
            recs.append("Improve structure with clear headings and bullet points for better ATS parsing.")
        if not recs:
            recs.append("Strong alignment detected. Minor refinements can further improve competitiveness.")
        return recs[:6]


ats_scorer = ATSScorer()