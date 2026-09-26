"""
Validation and Hallucination Guard to protect against hallucinations,
URLs, category taboo violations, and compliance issues.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


URL_REGEX = re.compile(r"(https?://\S+|www\.\S+|\b\w+\.(?:com|org|in|net|co|io|ai)\b/\S*)", re.IGNORECASE)

INTERNAL_JARGON = [
    r"\bcontext\b", r"\btrigger\b", r"\bllm\b", r"\bdataset\b", r"\bjudge\b",
    r"\bprompt\b", r"\bjson\b", r"\bpayload\b", r"\balgorithm\b", r"\bdataclass\b"
]
COMPILED_JARGON = [re.compile(p, re.IGNORECASE) for p in INTERNAL_JARGON]

CATEGORY_TABOOS: Dict[str, List[str]] = {
    "dentists": ["guaranteed", "100% safe", "completely cure", "miracle", "best in city", "doctor approved"],
    "salons": ["guaranteed glow", "permanent results", "instant transformation", "miracle", "best in city"],
    "restaurants": ["best food in city", "guaranteed packed house", "miracle marketing", "viral guarantee"],
    "gyms": ["guaranteed weight loss", "shred in 7 days", "miracle transformation", "fastest results"],
    "pharmacies": ["miracle cure", "guaranteed result", "100% safe"]
}


class HallucinationGuard:
    @staticmethod
    def sanitize_urls(text: str) -> str:
        return URL_REGEX.sub("", text).strip()

    strip_urls = sanitize_urls

    @staticmethod
    def check_taboos(text: str, category_slug: Optional[str]) -> Tuple[bool, List[str]]:
        if not category_slug:
            return False, []
        taboos = CATEGORY_TABOOS.get(category_slug.lower(), [])
        found = []
        text_lower = text.lower()
        for taboo in taboos:
            if taboo.lower() in text_lower:
                found.append(taboo)
        return len(found) > 0, found

    @staticmethod
    def clean_taboos(text: str, category_slug: Optional[str]) -> str:
        if not category_slug:
            return text
        taboos = CATEGORY_TABOOS.get(category_slug.lower(), [])
        cleaned = text
        for taboo in taboos:
            pattern = re.compile(re.escape(taboo), re.IGNORECASE)
            if "guaranteed" in taboo.lower():
                cleaned = pattern.sub("proven", cleaned)
            elif "miracle" in taboo.lower():
                cleaned = pattern.sub("effective", cleaned)
            elif "100% safe" in taboo.lower():
                cleaned = pattern.sub("well-tested", cleaned)
            elif "best in city" in taboo.lower() or "best food" in taboo.lower():
                cleaned = pattern.sub("highly-rated", cleaned)
            else:
                cleaned = pattern.sub("trusted", cleaned)
        return cleaned

    @staticmethod
    def check_internal_jargon(text: str) -> Tuple[bool, List[str]]:
        found = []
        for pat in COMPILED_JARGON:
            if pat.search(text):
                found.append(pat.pattern)
        return len(found) > 0, found

    @staticmethod
    def validate_and_sanitize(body: str, category_slug: Optional[str] = None) -> str:
        clean_body = HallucinationGuard.sanitize_urls(body)
        clean_body = HallucinationGuard.clean_taboos(clean_body, category_slug)
        clean_body = re.sub(r" +", " ", clean_body)
        clean_body = re.sub(r"\n{3,}", "\n\n", clean_body)
        return clean_body.strip()
