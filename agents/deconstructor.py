# agents/deconstructor.py
import json
import os
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from state import FactCheckerState, SubClaim


def deconstructor_node(state: FactCheckerState) -> Dict[str, Any]:
    """Break the original claim into atomic, independently verifiable sub-claims."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    system_prompt = (
        "You are an expert logician and fact-checker. Your job is to break down complex claims "
        "into their smallest independently verifiable atomic sub-claims. Each sub-claim must be "
        "a single, specific, falsifiable statement."
    )

    user_prompt = f"""Original claim: "{state['original_claim']}"

Decompose this into 3-6 atomic sub-claims. Each must be:
- A single verifiable statement
- Specific enough to search for evidence
- Not a value judgment or opinion

Respond ONLY with a JSON array:
[
  {{"id": 1, "text": "sub-claim text here"}},
  {{"id": 2, "text": "sub-claim text here"}}
]"""

    sub_claims: List[SubClaim] = []

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        raw = response.content.strip()
        # Strip ```json fences
        if raw.startswith("```"):
            raw = raw.lstrip("`")
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        parsed = json.loads(raw)
        for item in parsed:
            sub_claims.append(SubClaim(
                id=item["id"],
                text=item["text"],
                verdict=None,
                confidence=0,
                supporting_sources=[],
                contradicting_sources=[],
                reasoning="",
                needs_deeper_research=False,
            ))
    except Exception as e:
        print(f"[deconstructor_node] JSON parse error: {e}. Falling back to single sub-claim.")
        sub_claims = [SubClaim(
            id=1,
            text=state["original_claim"],
            verdict=None,
            confidence=0,
            supporting_sources=[],
            contradicting_sources=[],
            reasoning="",
            needs_deeper_research=False,
        )]

    return {"sub_claims": sub_claims, "iteration_count": 0}
