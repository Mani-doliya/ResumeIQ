import re
from typing import Optional, List
import logging

from app.models.schemas import CandidateProfile
from app.utils.nlp_utils import (
    extract_emails, extract_phones, extract_name_heuristic,
    extract_years_experience, clean_text
)
from app.services.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class ResumeParser:
    SECTION_HEADERS = {
        "summary": ["summary", "professional summary", "profile", "about me", "objective"],
        "experience": ["experience", "work experience", "professional experience", "employment", "work history"],
        "education": ["education", "academic", "qualifications", "degrees"],
        "skills": ["skills", "technical skills", "core competencies", "technologies", "expertise"],
        "projects": ["projects", "personal projects", "key projects"],
        "certifications": ["certifications", "certificates", "licenses"]
    }

    def parse(self, raw_text: str) -> CandidateProfile:
        if not raw_text or len(raw_text.strip()) < 50:
            raise ValueError("Resume text is too short or empty")

        emails = extract_emails(raw_text)
        phones = extract_phones(raw_text)
        name = extract_name_heuristic(raw_text)
        years = extract_years_experience(raw_text)
        skills = skill_extractor.extract_skills(raw_text)
        education = self._extract_education(raw_text)
        summary = self._extract_summary(raw_text)

        return CandidateProfile(
            name=name,
            email=emails[0] if emails else None,
            phone=phones[0] if phones else None,
            summary=summary,
            experience_years=years,
            education=education,
            extracted_skills=skills,
            raw_text_length=len(raw_text)
        )

    def _extract_summary(self, text: str) -> Optional[str]:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            lower = line.strip().lower()
            if any(h in lower for h in self.SECTION_HEADERS["summary"]):
                summary_lines = []
                for j in range(i + 1, min(i + 8, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    if self._is_section_header(next_line):
                        break
                    summary_lines.append(next_line)
                if summary_lines:
                    return " ".join(summary_lines)[:500]
        return None

    def _extract_education(self, text: str) -> List[str]:
        education = []
        degree_patterns = [
            r'(bachelor[\'s]*\s*(?:of\s*)?(?:science|arts|engineering|technology|computer)?[^,\n]{0,40})',
            r'(master[\'s]*\s*(?:of\s*)?(?:science|arts|engineering|technology|business)?[^,\n]{0,40})',
            r'(ph\.?d\.?[^,\n]{0,40})',
            r'(b\.?tech\.?[^,\n]{0,40})',
            r'(m\.?tech\.?[^,\n]{0,40})',
            r'(b\.?e\.?[^,\n]{0,40})',
            r'(m\.?s\.?[^,\n]{0,30})',
            r'(b\.?s\.?[^,\n]{0,30})',
            r'(mba[^,\n]{0,30})',
        ]
        text_lower = text.lower()
        for pat in degree_patterns:
            matches = re.findall(pat, text_lower, re.IGNORECASE)
            for m in matches:
                cleaned = m.strip().title()
                if cleaned and cleaned not in education:
                    education.append(cleaned)
        return education[:5]

    def _is_section_header(self, line: str) -> bool:
        lower = line.strip().lower()
        if len(lower) > 50:
            return False
        for headers in self.SECTION_HEADERS.values():
            if any(h == lower or lower.startswith(h) for h in headers):
                return True
        return False


resume_parser = ResumeParser()