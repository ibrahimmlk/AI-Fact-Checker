# agents/evaluator.py
import copy
import json
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI

from state import FactCheckerState, SubClaim, VerdictType
from utils.formatting import format_sources


def evaluator_node(state: FactCheckerState) -> Dict[str, Any]:
    """Evaluate each sub-claim and assign a verdict with confidence score."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    updated_sub_claims: List[SubClaim] = []

    for sc in state["sub_claims"]:
        sc_copy = copy.deepcopy(sc)

        system_prompt = (
            "You are a rigorous fact-checker with expertise in epistemology and source evaluation. "
            "You evaluate claims based on evidence quality, source credibility, consensus, and logical consistency."
        )

        user_prompt = f"""Sub-claim: "{sc['text']}"

Supporting evidence:
{format_sources(sc.get('supporting_sources', []))}

Contradicting evidence:
{format_sources(sc.get('contradicting_sources', []))}

Evaluate this sub-claim and respond ONLY with JSON:
{{
  "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIABLE|DISPUTED",
  "confidence": <integer 0-100>,
  "reasoning": "<one paragraph explanation citing specific sources>",
  "needs_deeper_research": <true if confidence < 60 and more evidence could exist, else false>
}}

Verdict definitions:
- TRUE: Claim is accurate based on available evidence
- FALSE: Claim is factually incorrect based on available evidence
- MISLEADING: Claim is technically true but omits crucial context
- UNVERIFIABLE: Insufficient credible evidence to determine truth
- DISPUTED: Credible sources actively disagree"""

        try:
            response = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.lstrip("`")
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()

            parsed = json.loads(raw)
            sc_copy["verdict"] = parsed.get("verdict", "UNVERIFIABLE")
            sc_copy["confidence"] = int(parsed.get("confidence", 0))
            sc_copy["reasoning"] = parsed.get("reasoning", "")
            sc_copy["needs_deeper_research"] = bool(parsed.get("needs_deeper_research", False))
        except Exception as e:
            print(f"[evaluator_node] Error evaluating sub-claim {sc['id']}: {e}")
            sc_copy["verdict"] = "UNVERIFIABLE"
            sc_copy["confidence"] = 0
            sc_copy["reasoning"] = "Evaluation failed due to a processing error."
            sc_copy["needs_deeper_research"] = False

        updated_sub_claims.append(sc_copy)

    # Compute overall verdict
    overall_verdict = _compute_overall_verdict(updated_sub_claims)
    credibility_score = _compute_credibility_score(updated_sub_claims)

    return {
        "sub_claims": updated_sub_claims,
        "overall_verdict": overall_verdict,
        "credibility_score": credibility_score,
    }


def _compute_overall_verdict(sub_claims: List[SubClaim]) -> VerdictType:
    if not sub_claims:
        return "UNVERIFIABLE"

    verdicts = [sc.get("verdict", "UNVERIFIABLE") for sc in sub_claims]
    total = len(verdicts)

    false_count = verdicts.count("FALSE")
    true_count = verdicts.count("TRUE")
    misleading_count = verdicts.count("MISLEADING")
    unverifiable_count = verdicts.count("UNVERIFIABLE")

    if false_count > 0:
        return "FALSE"
    if true_count > total / 2:
        return "TRUE"
    if misleading_count > 0 and false_count == 0:
        return "MISLEADING"
    if unverifiable_count > total / 2:
        return "UNVERIFIABLE"
    return "DISPUTED"


def _compute_credibility_score(sub_claims: List[SubClaim]) -> int:
    if not sub_claims:
        return 0
    total_confidence = sum(sc.get("confidence", 0) for sc in sub_claims)
    return int(total_confidence / len(sub_claims))
