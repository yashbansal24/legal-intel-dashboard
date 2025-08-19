import re
from typing import Optional, Sequence, Dict

AGREEMENT_TYPES = [
    "NDA", "Non-Disclosure Agreement", "MSA", "Master Services Agreement",
    "Franchise Agreement", "Supplier Agreement", "Employment Agreement"
]
JURISDICTIONS = ["UAE", "UK", "Delaware", "US", "EU", "KSA", "Dubai", "Abu Dhabi"]
GEOGRAPHIES = ["Middle East", "Europe", "Asia", "GCC", "United States"]
INDUSTRIES = ["Oil & Gas", "Healthcare", "Technology", "Finance", "Retail"]

def _find_first(tokens: Sequence[str], text: str) -> Optional[str]:
    for t in tokens:
        if re.search(rf"\b{re.escape(t)}\b", text, flags=re.I):
            return t if len(t) < 40 else t[:40]
    return None

def extract_metadata(text: str) -> dict:
    # Very simple heuristics using regular expressions
    agreement_type = _find_first(AGREEMENT_TYPES, text) or "Unknown"
    governing_law = _find_first(JURISDICTIONS, text)
    geography = _find_first(GEOGRAPHIES, text)
    industry = _find_first(INDUSTRIES, text)
    return {
        "agreement_type": "NDA" if "non-disclosure" in text.lower() else agreement_type,
        "governing_law": governing_law,
        "geography": geography,
        "industry": industry,
    }
