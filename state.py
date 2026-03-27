# state.py
from typing import TypedDict, List, Literal, Optional

VerdictType = Literal["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE", "DISPUTED"]

class SubClaim(TypedDict):
    id: int
    text: str
    verdict: Optional[VerdictType]
    confidence: int
    supporting_sources: List[dict]
    contradicting_sources: List[dict]
    reasoning: str
    needs_deeper_research: bool

class Fallacy(TypedDict):
    name: str
    description: str
    severity: Literal["low", "medium", "high"]

class FactCheckerState(TypedDict):
    original_claim: str
    sub_claims: List[SubClaim]
    fallacies: List[Fallacy]
    overall_verdict: Optional[VerdictType]
    credibility_score: int
    executive_summary: str
    final_report: str
    iteration_count: int
    error: str
