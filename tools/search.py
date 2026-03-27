# tools/search.py
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client: TavilyClient | None = None

def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set in environment")
        _client = TavilyClient(api_key=api_key)
    return _client


def search_for_evidence(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search Tavily for evidence on a query. Returns list of {url, title, content, score}."""
    try:
        client = _get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )
        results = []
        for r in response.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
            })
        return results
    except Exception as e:
        print(f"[search_for_evidence] Error searching for '{query}': {e}")
        return []


def search_supporting(claim: str) -> List[Dict[str, Any]]:
    """Search for evidence supporting a claim."""
    query = f"{claim} evidence proof confirmed"
    return search_for_evidence(query, max_results=4)


def search_contradicting(claim: str) -> List[Dict[str, Any]]:
    """Search for evidence contradicting a claim."""
    query = f"{claim} false debunked misleading fact check"
    return search_for_evidence(query, max_results=4)


def search_neutral(claim: str) -> List[Dict[str, Any]]:
    """Search for neutral analysis and context on a claim."""
    query = f"{claim} analysis context"
    return search_for_evidence(query, max_results=3)
