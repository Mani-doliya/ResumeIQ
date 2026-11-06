from typing import List, Dict, Tuple
import logging
from collections import Counter

from app.services.skill_extractor import skill_extractor
from app.utils.nlp_utils import clean_text, tokenize

logger = logging.getLogger(__name__)


class DomainClassifier:
    DOMAIN_KEYWORDS = {
        "Machine Learning / AI": [
            "machine learning", "deep learning", "neural network", "tensorflow", "pytorch",
            "scikit-learn", "xgboost", "nlp", "computer vision", "llm", "transformer",
            "model training", "feature engineering", "mlops", "data science"
        ],
        "Software Engineering": [
            "software engineer", "backend", "frontend", "full stack", "api", "microservices",
            "rest", "java", "spring", "node.js", "react", "angular", "system design"
        ],
        "Data Engineering": [
            "data engineer", "etl", "pipeline", "spark", "hadoop", "kafka", "airflow",
            "data warehouse", "snowflake", "bigquery", "databricks"
        ],
        "Cloud / DevOps": [
            "devops", "aws", "azure", "gcp", "kubernetes", "docker", "terraform",
            "ci/cd", "infrastructure", "sre", "cloud architect"
        ],
        "Data Analysis": [
            "data analyst", "business intelligence", "tableau", "power bi", "sql",
            "excel", "dashboard", "reporting", "statistics"
        ],
        "Product / Management": [
            "product manager", "project manager", "agile", "scrum", "roadmap",
            "stakeholder", "product owner"
        ]
    }

    def classify(self, text: str, skills: List[str]) -> Tuple[str, float, List[Dict[str, float]]]:
        if not text:
            return "General", 0.0, []

        text_lower = clean_text(text)
        scores: Dict[str, float] = {}

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = 0.0
            for kw in keywords:
                if kw in text_lower:
                    score += 2.0
                elif any(part in text_lower for part in kw.split()):
                    score += 0.5
            for skill in skills:
                skill_l = skill.lower()
                for kw in keywords:
                    if skill_l in kw or kw in skill_l:
                        score += 1.5
            scores[domain] = score

        if not any(scores.values()):
            return "General", 0.0, [{"domain": "General", "confidence": 0.0}]

        total = sum(scores.values()) or 1.0
        normalized = {d: round(s / total * 100, 2) for d, s in scores.items()}
        sorted_domains = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        top_domain, confidence = sorted_domains[0]
        top_list = [{"domain": d, "confidence": c} for d, c in sorted_domains[:4]]
        return top_domain, confidence, top_list


domain_classifier = DomainClassifier()