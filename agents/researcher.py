# agents/researcher.py
import copy
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from state import FactCheckerState, SubClaim
from tools.search import search_supporting, search_contradicting, search_neutral


def researcher_node(state: FactCheckerState) -> Dict[str, Any]:
    """Search for supporting and contradicting evidence for each sub-claim."""
    updated_sub_claims: List[SubClaim] = []

    for sc in state["sub_claims"]:
        sc_copy = copy.deepcopy(sc)

        try:
            supporting = search_supporting(sc["text"])
        except Exception as e:
            print(f"[researcher_node] Error in search_supporting for sub-claim {sc['id']}: {e}")
            supporting = []

        try:
            contradicting = search_contradicting(sc["text"])
        except Exception as e:
            print(f"[researcher_node] Error in search_contradicting for sub-claim {sc['id']}: {e}")
            contradicting = []

        try:
            neutral = search_neutral(sc["text"])
        except Exception as e:
            print(f"[researcher_node] Error in search_neutral for sub-claim {sc['id']}: {e}")
            neutral = []

        # Merge neutral into supporting or contradicting based on content keywords
        for ns in neutral:
            content_lower = ns.get("content", "").lower()
            if any(kw in content_lower for kw in ["false", "debunk", "mislead", "incorrect", "wrong", "myth"]):
                contradicting.append(ns)
            else:
                supporting.append(ns)

        # Truncate content to 1500 chars
        for s in supporting:
            s["content"] = s.get("content", "")[:1500]
        for s in contradicting:
            s["content"] = s.get("content", "")[:1500]

        sc_copy["supporting_sources"] = supporting
        sc_copy["contradicting_sources"] = contradicting
        updated_sub_claims.append(sc_copy)

    return {"sub_claims": updated_sub_claims}
