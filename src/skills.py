"""Skill extraction utilities and curated skill list."""

import preprocessing
from typing import Dict, Set

SKILLS = [
    "python", "java", "c", "c++", "c#",
    "machine learning", "deep learning", "nlp",
    "sql", "nosql", "postgresql", "mysql",
    "docker", "kubernetes", "aws", "azure", "gcp",
    "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "keras",
    ".net", "node.js"
]

def _normalize_skill(skill: str) -> str:
    """Normalize a skill to match the preprocessing pipeline."""
    return preprocessing.clean_text(skill)

_NORMALIZED_TO_DISPLAY: Dict[str, str] = {}
for skill in SKILLS:
    normalized = _normalize_skill(skill)
    if normalized:
        _NORMALIZED_TO_DISPLAY.setdefault(normalized, skill)

_SINGLE_TOKEN = {key for key in _NORMALIZED_TO_DISPLAY.keys() if " " not in key}
_MULTI_TOKEN = {key for key in _NORMALIZED_TO_DISPLAY.keys() if " " in key}

# text is resume or job (already cleaned)
def extract_skills(text: str) -> Set[str]:
    """Extract skills from cleaned text produced by preprocessing.clean_text."""
    found = set()
    if not text:
        return found

    words = set(text.split())

    for normalized in _SINGLE_TOKEN:
        if normalized in words:
            found.add(_NORMALIZED_TO_DISPLAY[normalized])

    for normalized in _MULTI_TOKEN:
        if normalized in text:
            found.add(_NORMALIZED_TO_DISPLAY[normalized])

    return found




