from collections import Counter
from typing import Iterable
from app.models.document import Document

def build_dashboard(docs: Iterable[Document]) -> dict:
    agreement_types = Counter([d.agreement_type or "Unknown" for d in docs])
    jurisdictions = Counter([d.governing_law or "Unknown" for d in docs])
    industries = Counter([d.industry or "Unknown" for d in docs])
    geographies = Counter([d.geography or "Unknown" for d in docs])
    return {
        "agreement_types": dict(agreement_types),
        "jurisdictions": dict(jurisdictions),
        "industries": dict(industries),
        "geographies": dict(geographies),
        "count_documents": len(list(docs)),
    }
