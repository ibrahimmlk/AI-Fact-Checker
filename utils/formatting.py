# utils/formatting.py
from typing import List, Dict, Any


def format_sources(sources: List[Dict[str, Any]]) -> str:
    """Format sources list into readable text for LLM prompts."""
    if not sources:
        return "No sources found."
    lines = []
    for i, s in enumerate(sources[:5], 1):
        lines.append(f"[{i}] {s.get('title', 'No title')} ({s.get('url', '')})")
        lines.append(f"    {s.get('content', '')[:400]}")
    return "\n".join(lines)


def format_sub_claims_for_writer(sub_claims: List[Dict[str, Any]]) -> str:
    """Format all sub-claims with their verdicts for the writer agent."""
    lines = []
    for sc in sub_claims:
        lines.append(f"Sub-claim {sc['id']}: {sc['text']}")
        lines.append(f"  Verdict: {sc.get('verdict', 'UNVERIFIABLE')} (confidence: {sc.get('confidence', 0)}%)")
        lines.append(f"  Reasoning: {sc.get('reasoning', '')}")
        lines.append(f"  Supporting URLs: {[s['url'] for s in sc.get('supporting_sources', [])][:3]}")
        lines.append(f"  Contradicting URLs: {[s['url'] for s in sc.get('contradicting_sources', [])][:3]}")
        lines.append("")
    return "\n".join(lines)


def format_fallacies(fallacies: List[Dict[str, Any]]) -> str:
    """Format fallacies list for the writer agent."""
    if not fallacies:
        return "No logical fallacies detected."
    lines = []
    for f in fallacies:
        lines.append(f"- {f['name']} (severity: {f['severity']}): {f['description']}")
    return "\n".join(lines)


def verdict_color(verdict: str) -> str:
    """Return Streamlit-compatible color string for a verdict."""
    colors = {
        "TRUE": "green",
        "FALSE": "red",
        "MISLEADING": "orange",
        "UNVERIFIABLE": "gray",
        "DISPUTED": "blue",
    }
    return colors.get(verdict, "gray")


def verdict_emoji(verdict: str) -> str:
    """Return emoji for a verdict."""
    emojis = {
        "TRUE": "✅",
        "FALSE": "❌",
        "MISLEADING": "⚠️",
        "UNVERIFIABLE": "❓",
        "DISPUTED": "⚖️",
    }
    return emojis.get(verdict, "❓")


def confidence_label(score: int) -> str:
    """Human-readable confidence label."""
    if score >= 85:
        return "Very High"
    if score >= 70:
        return "High"
    if score >= 50:
        return "Moderate"
    if score >= 30:
        return "Low"
    return "Very Low"


def severity_color(severity: str) -> str:
    """Return Streamlit-compatible color string for a fallacy severity."""
    colors = {"low": "blue", "medium": "orange", "high": "red"}
    return colors.get(severity, "gray")
