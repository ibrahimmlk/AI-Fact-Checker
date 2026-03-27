# agents/writer.py
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from state import FactCheckerState
from utils.formatting import format_sub_claims_for_writer, format_fallacies


def writer_node(state: FactCheckerState) -> Dict[str, Any]:
    """Generate the comprehensive fact-check report and executive summary."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    system_prompt = (
        "You are a professional fact-checking journalist. You write clear, evidence-based "
        "fact-check reports that are accessible to general audiences while maintaining rigour."
    )

    user_prompt = f"""Write a comprehensive fact-check report based on this analysis.

Original claim: "{state['original_claim']}"
Overall verdict: {state.get('overall_verdict', 'UNVERIFIABLE')}
Credibility score: {state.get('credibility_score', 0)}/100

Sub-claim analyses:
{format_sub_claims_for_writer(state.get('sub_claims', []))}

Logical issues detected:
{format_fallacies(state.get('fallacies', []))}

REPORT STRUCTURE (use exact markdown headers):
# Fact Check: [shortened claim, max 10 words]

## Overall Verdict: [VERDICT] — [score]/100

## Executive Summary
[2-3 sentences: what was claimed, what we found, bottom line]

## Claim Breakdown
[For each sub-claim: ### Sub-claim N: [text], then **Verdict:** X, **Confidence:** Y%, then explanation paragraph with inline citations]

## What the Evidence Shows
[Synthesised prose paragraph covering the strongest supporting and contradicting evidence]

## Logical & Rhetorical Issues
[If fallacies exist: describe each one and its impact. If none: state "No significant logical issues detected."]

## Context & Background
[1-2 paragraphs providing relevant context that helps understand why this claim exists]

## Bottom Line
[Final 2-3 sentence plain-English conclusion a non-expert can understand]

## Sources
[Numbered list of all unique URLs cited, grouped by sub-claim]"""

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        report = response.content.strip()
    except Exception as e:
        print(f"[writer_node] Error generating report: {e}")
        report = f"# Fact Check Report\n\nAn error occurred while generating the report: {e}"

    # Generate short executive summary
    summary_prompt = f"""Based on this fact-check:
Original claim: "{state['original_claim']}"
Overall verdict: {state.get('overall_verdict', 'UNVERIFIABLE')}
Credibility score: {state.get('credibility_score', 0)}/100

Write a 2-3 sentence executive summary in plain English with NO markdown formatting.
Focus on: what was claimed, what was found, and the bottom line."""

    try:
        summary_response = llm.invoke([
            {"role": "user", "content": summary_prompt}
        ])
        executive_summary = summary_response.content.strip()
    except Exception as e:
        print(f"[writer_node] Error generating executive summary: {e}")
        executive_summary = f"This claim received an overall verdict of {state.get('overall_verdict', 'UNVERIFIABLE')} with a credibility score of {state.get('credibility_score', 0)}/100."

    return {"final_report": report, "executive_summary": executive_summary}
