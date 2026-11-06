import re
from typing import List, Set, Optional
import logging

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "must", "shall", "can", "this", "that", "these", "those", "i", "you", "he", "she",
    "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
    "our", "their", "what", "which", "who", "whom", "whose", "where", "when", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "also", "now", "here", "there", "then", "once", "if", "about", "into",
    "through", "during", "before", "after", "above", "below", "up", "down", "out",
    "off", "over", "under", "again", "further", "then", "once"
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s\+\#\.\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    cleaned = clean_text(text)
    tokens = cleaned.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def extract_emails(text: str) -> List[str]:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def extract_phones(text: str) -> List[str]:
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    phones = []
    for p in patterns:
        phones.extend(re.findall(p, text))
    return list(set(phones))[:3]


def extract_name_heuristic(text: str) -> Optional[str]:
    lines = text.strip().split('\n')[:8]
    for line in lines:
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if re.search(r'@|http|www\.|linkedin|github|phone|email|mobile|\d{5,}', line.lower()):
            continue
        words = line.split()
        if 1 < len(words) <= 5 and all(w[0].isupper() or w.isupper() for w in words if w):
            return line
    return None


def extract_years_experience(text: str) -> Optional[float]:
    patterns = [
        r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
        r'experience\s*(?:of\s*)?(\d+\.?\d*)\+?\s*(?:years?|yrs?)',
        r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:in|as)',
    ]
    text_lower = text.lower()
    for p in patterns:
        match = re.search(p, text_lower)
        if match:
            try:
                years = float(match.group(1))
                if 0 < years < 50:
                    return years
            except ValueError:
                continue
    return None


def ngrams(tokens: List[str], n: int = 2) -> List[str]:
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]