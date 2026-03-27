# agents/deep_researcher.py
import copy
import json
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from state import FactCheckerState, SubClaim
from tools.search import search_for_evidence


def deep_researcher_node(state: FactCheckerState) -> Dict[str, Any]:
    """Perform targeted deep research for sub-claims with low confidence."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    updated_sub_claims: List[SubClaim] = []

    for sc in state["sub_claims"]:
        sc_copy = copy.deepcopy(sc)

        if not sc.get("needs_deeper_research", False):
            updated_sub_claims.append(sc_copy)
            continue

        existing_supporting_urls = [s["url"] for s in sc.get("supporting_sources", [])]
        existing_contradicting_urls = [s["url"] for s in sc.get("contradicting_sources", [])]

        query_prompt = f"""Sub-claim: {sc['text']}
Already found supporting: {existing_supporting_urls}
Already found contradicting: {existing_contradicting_urls}

Generate 2 highly specific search queries to find more definitive evidence.
Return ONLY a JSON array of 2 strings."""

        try:
            response = llm.invoke([
                {"role": "user", "content": query_prompt}
            ])
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.lstrip("`")
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()
            queries: List[str] = json.loads(raw)
        except Exception as e:
            print(f"[deep_researcher_node] Failed to generate queries for sub-claim {sc['id']}: {e}")
            queries = [sc["text"] + " scientific evidence", sc["text"] + " expert analysis fact check"]

        all_existing_urls = set(existing_supporting_urls + existing_contradicting_urls)

        for query in queries[:2]:
            try:
                new_results = search_for_evidence(query, max_results=4)
            except Exception as e:
                print(f"[deep_researcher_node] Error searching '{query}': {e}")
                new_results = []

            for result in new_results:
                url = result.get("url", "")
                if url in all_existing_urls:
                    continue
                all_existing_urls.add(url)
                result["content"] = result.get("content", "")[:1500]

                content_lower = result.get("content", "").lower()
                if any(kw in content_lower for kw in ["false", "debunk", "mislead", "incorrect", "wrong", "myth"]):
                    sc_copy["contradicting_sources"].append(result)
                else:
                    sc_copy["supporting_sources"].append(result)

        sc_copy["needs_deeper_research"] = False
        updated_sub_claims.append(sc_copy)

    return {
        "sub_claims": updated_sub_claims,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
