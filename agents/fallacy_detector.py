# agents/fallacy_detector.py
import json
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from state import FactCheckerState, Fallacy


def fallacy_detector_node(state: FactCheckerState) -> Dict[str, Any]:
    """Detect logical fallacies and manipulation techniques in the original claim."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    system_prompt = (
        "You are an expert in rhetoric, logic, and critical thinking. "
        "Identify logical fallacies, manipulation techniques, and rhetorical devices used in claims."
    )

    user_prompt = f"""Analyze this claim for logical fallacies and manipulation techniques:

"{state['original_claim']}"

Respond ONLY with a JSON array (empty array [] if none found):
[
  {{
    "name": "Fallacy name",
    "description": "How this fallacy appears specifically in this claim",
    "severity": "low|medium|high"
  }}
]

Common fallacies to check: Appeal to Authority, False Dichotomy, Slippery Slope,
Ad Hominem, Straw Man, Cherry Picking, Hasty Generalization, Correlation/Causation,
Bandwagon, Appeal to Emotion, Loaded Language, False Equivalence, Anecdotal Evidence.
Only include fallacies that are genuinely present. Return [] if the claim is straightforward."""

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

        fallacies: List[Fallacy] = json.loads(raw)
        return {"fallacies": fallacies}
    except Exception as e:
        print(f"[fallacy_detector_node] Error detecting fallacies: {e}")
        return {"fallacies": []}
