import re
from pathlib import Path
from typing import List, Set, Dict, Tuple
import logging
from collections import defaultdict

from openpyxl import load_workbook, Workbook
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.core.config import SKILLS_TAXONOMY_PATH
from app.utils.nlp_utils import clean_text, tokenize, ngrams

logger = logging.getLogger(__name__)


class SkillExtractor:
    def __init__(self):
        self.skills_by_domain: Dict[str, Set[str]] = {}
        self.all_skills: Set[str] = set()
        self.skill_aliases: Dict[str, str] = {}
        self._load_or_create_taxonomy()

    def _load_or_create_taxonomy(self) -> None:
        if SKILLS_TAXONOMY_PATH.exists():
            try:
                wb = load_workbook(SKILLS_TAXONOMY_PATH, read_only=True)
                ws = wb.active
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not row or not row[0]:
                        continue
                    skill = str(row[0]).strip().lower()
                    domain = str(row[1]).strip() if row[1] else "General"
                    aliases = str(row[2]).strip().lower() if len(row) > 2 and row[2] else ""
                    self.all_skills.add(skill)
                    if domain not in self.skills_by_domain:
                        self.skills_by_domain[domain] = set()
                    self.skills_by_domain[domain].add(skill)
                    self.skill_aliases[skill] = skill
                    if aliases:
                        for alias in aliases.split(","):
                            alias = alias.strip()
                            if alias:
                                self.skill_aliases[alias] = skill
                wb.close()
                logger.info(f"Loaded {len(self.all_skills)} skills from taxonomy")
                return
            except Exception as e:
                logger.warning(f"Failed to load taxonomy: {e}. Creating default.")
        self._create_default_taxonomy()

    def _create_default_taxonomy(self) -> None:
        default_data = {
            "Programming Languages": [
                "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
                "scala", "kotlin", "ruby", "php", "swift", "r", "matlab", "sql"
            ],
            "Machine Learning": [
                "machine learning", "deep learning", "neural networks", "supervised learning",
                "unsupervised learning", "reinforcement learning", "transfer learning",
                "feature engineering", "model evaluation", "hyperparameter tuning",
                "cross validation", "ensemble methods", "gradient boosting", "xgboost",
                "lightgbm", "catboost", "random forest", "svm", "knn", "naive bayes"
            ],
            "Deep Learning Frameworks": [
                "tensorflow", "pytorch", "keras", "jax", "mxnet", "caffe", "onnx"
            ],
            "NLP": [
                "nlp", "natural language processing", "transformers", "bert", "gpt",
                "llm", "large language models", "huggingface", "spacy", "nltk",
                "word2vec", "tf-idf", "named entity recognition", "sentiment analysis",
                "text classification", "topic modeling", "rag", "embeddings"
            ],
            "Computer Vision": [
                "computer vision", "opencv", "yolo", "object detection", "image classification",
                "cnn", "resnet", "efficientnet", "segmentation", "ocr"
            ],
            "Data Science": [
                "data science", "data analysis", "pandas", "numpy", "scipy", "matplotlib",
                "seaborn", "plotly", "data visualization", "statistical analysis",
                "a/b testing", "hypothesis testing", "eda", "feature selection"
            ],
            "MLOps": [
                "mlops", "model deployment", "model monitoring", "mlflow", "kubeflow",
                "airflow", "docker", "kubernetes", "ci/cd", "model serving",
                "fastapi", "flask", "streamlit", "gradio"
            ],
            "Cloud & Big Data": [
                "aws", "azure", "gcp", "s3", "ec2", "lambda", "spark", "hadoop",
                "kafka", "airflow", "databricks", "snowflake", "redshift", "bigquery"
            ],
            "Databases": [
                "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
                "dynamodb", "sqlite", "oracle", "sql server"
            ],
            "Soft Skills": [
                "leadership", "communication", "teamwork", "problem solving",
                "project management", "agile", "scrum", "mentoring"
            ],
            "Tools": [
                "git", "github", "gitlab", "jira", "confluence", "linux", "bash",
                "jupyter", "vs code", "pycharm", "tableau", "power bi"
            ]
        }
        wb = Workbook()
        ws = wb.active
        ws.title = "Skills"
        ws.append(["Skill", "Domain", "Aliases"])
        for domain, skills in default_data.items():
            self.skills_by_domain[domain] = set()
            for skill in skills:
                skill_l = skill.lower()
                self.all_skills.add(skill_l)
                self.skills_by_domain[domain].add(skill_l)
                self.skill_aliases[skill_l] = skill_l
                ws.append([skill, domain, ""])
        SKILLS_TAXONOMY_PATH.parent.mkdir(parents=True, exist_ok=True)
        wb.save(SKILLS_TAXONOMY_PATH)
        logger.info(f"Created default taxonomy with {len(self.all_skills)} skills")

    def extract_skills(self, text: str) -> List[str]:
        if not text:
            return []
        cleaned = clean_text(text)
        tokens = tokenize(text)
        bigrams = ngrams(tokens, 2)
        trigrams = ngrams(tokens, 3)
        candidates = set(tokens + bigrams + trigrams)

        found: Set[str] = set()
        for cand in candidates:
            if cand in self.skill_aliases:
                found.add(self.skill_aliases[cand])
            elif cand in self.all_skills:
                found.add(cand)

        for skill in self.all_skills:
            if len(skill) > 3 and skill in cleaned:
                found.add(skill)

        multi_word = [s for s in self.all_skills if ' ' in s]
        for skill in multi_word:
            if skill in cleaned:
                found.add(skill)

        return sorted(list(found))

    def get_skills_by_domain(self, skills: List[str]) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = defaultdict(list)
        skill_set = set(skills)
        for domain, domain_skills in self.skills_by_domain.items():
            matched = sorted(skill_set & domain_skills)
            if matched:
                result[domain] = matched
        return dict(result)

    def compute_skill_overlap(self, resume_skills: List[str], jd_skills: List[str]) -> Tuple[List[str], List[str], float]:
        r_set = set(s.lower() for s in resume_skills)
        j_set = set(s.lower() for s in jd_skills)
        matched = sorted(r_set & j_set)
        missing = sorted(j_set - r_set)
        if not j_set:
            pct = 0.0
        else:
            pct = round(len(matched) / len(j_set) * 100, 2)
        return matched, missing, pct


skill_extractor = SkillExtractor()