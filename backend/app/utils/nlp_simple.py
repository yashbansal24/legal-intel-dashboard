import re
from typing import Dict, Optional

PLACE_ALIASES: Dict[str, str] = {
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "ksa": "Saudi Arabia",
    "saudi": "Saudi Arabia",
    "us": "United States",
    "usa": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "delaware": "Delaware",
    "california": "California",
    "dubai": "Dubai",
    "abu dhabi": "Abu Dhabi",
    "europe": "Europe",
    "gcc": "GCC",
}

# common phrasings: "governed by X law", "under X law", "valid in X", "applicable in X"
PATTERNS = [
    r"governed by (?P<place>[a-zA-Z\s]+?) law",
    r"under (?P<place>[a-zA-Z\s]+?) law",
    r"valid in (?P<place>[a-zA-Z\s]+)",
    r"applicable in (?P<place>[a-zA-Z\s]+)",
    r"in (?P<place>[a-zA-Z\s]+)$",
    r"(?P<place>[a-zA-Z\s]+) law",
]

def _normalize_place(raw: str) -> Optional[str]:
    key = raw.strip().lower()
    if key in PLACE_ALIASES:
        return PLACE_ALIASES[key]
    # try word-by-word collapse (e.g., "u a e")
    collapsed = key.replace(".", "").replace(" ", "")
    if collapsed in ("uae", "usa", "uk", "ksa"):
        return PLACE_ALIASES.get(collapsed, raw.strip())
    # capitalize words otherwise
    return " ".join(w.capitalize() for w in raw.strip().split()) if raw.strip() else None

def extract_filters(question: str) -> Dict[str, str]:
    """
    Returns a dict of filters we can apply to Document fields.
    Supported keys: governing_law, geography
    """
    q = question.lower().strip()
    # 1) explicit patterns
    for pat in PATTERNS:
        m = re.search(pat, q)
        if m and m.group("place"):
            place = _normalize_place(m.group("place"))
            if place:
                # if phrased as 'law', prefer governing_law; otherwise geography
                if "law" in pat or "law" in q:
                    return {"governing_law": place}
                return {"geography": place}
    # 2) fall back: scan tokens and map to a known place
    for alias in sorted(PLACE_ALIASES.keys(), key=len, reverse=True):
        if alias in q:
            place = PLACE_ALIASES[alias]
            # prefer governing_law if question mentions 'law'
            if "law" in q or "governed" in q or "under" in q:
                return {"governing_law": place}
            return {"geography": place}
    return {}  # no filters
