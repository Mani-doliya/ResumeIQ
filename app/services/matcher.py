from typing import List, Tuple, Dict
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.skill_extractor import skill_extractor
from app.utils.nlp_utils import clean_text, tokenize

logger = logging.getLogger(__name__)


class ResumeMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1,
            sublinear_tf=True
        )

    def compute_similarity(self, resume_text: str, jd_text: str) -> float:
        if not resume_text or not jd_text:
            return 0.0
        try:
            corpus = [clean_text(resume_text), clean_text(jd_text)]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(round(sim * 100, 2))
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0

    def extract_matched_keywords(self, resume_text: str, jd_text: str, top_k: int = 20) -> List[str]:
        try:
            corpus = [clean_text(resume_text), clean_text(jd_text)]
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=3000)
            matrix = vectorizer.fit_transform(corpus)
            feature_names = vectorizer.get_feature_names_out()
            resume_vec = matrix[0].toarray().flatten()
            jd_vec = matrix[1].toarray().flatten()
            common_scores = resume_vec * jd_vec
            top_indices = np.argsort(common_scores)[::-1][:top_k]
            keywords = [feature_names[i] for i in top_indices if common_scores[i] > 0]
            return keywords
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []

    def rank_candidate(
        self,
        similarity: float,
        skill_match_pct: float,
        experience_years: float | None,
        has_contact: bool,
        text_length: int
    ) -> float:
        weights = {
            "similarity": 0.35,
            "skills": 0.35,
            "experience": 0.15,
            "completeness": 0.15
        }
        exp_score = 0.0
        if experience_years is not None:
            exp_score = min(experience_years / 10.0, 1.0) * 100

        completeness = 0.0
        if has_contact:
            completeness += 40
        if text_length > 500:
            completeness += 30
        if text_length > 1500:
            completeness += 30

        ranking = (
            weights["similarity"] * similarity +
            weights["skills"] * skill_match_pct +
            weights["experience"] * exp_score +
            weights["completeness"] * completeness
        )
        return round(min(ranking, 100.0), 2)

    def evaluate_matching(
        self,
        predicted_skills: List[str],
        ground_truth_skills: List[str]
    ) -> Dict[str, float]:
        pred = set(s.lower() for s in predicted_skills)
        truth = set(s.lower() for s in ground_truth_skills)
        if not truth:
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0}
        tp = len(pred & truth)
        precision = tp / len(pred) if pred else 0.0
        recall = tp / len(truth) if truth else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }


resume_matcher = ResumeMatcher()