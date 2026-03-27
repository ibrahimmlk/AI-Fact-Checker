# graph.py
from langgraph.graph import StateGraph, END

from state import FactCheckerState
from agents.deconstructor import deconstructor_node
from agents.researcher import researcher_node
from agents.deep_researcher import deep_researcher_node
from agents.evaluator import evaluator_node
from agents.fallacy_detector import fallacy_detector_node
from agents.writer import writer_node

MAX_ITERATIONS = 2


def should_dig_deeper(state: FactCheckerState) -> str:
    """
    Conditional router: checks if any sub-claim needs deeper research.
    Returns 'deep_research' to loop back, or 'proceed' to continue.
    Max 2 iterations to prevent infinite loops.
    """
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        return "proceed"

    needs_more = any(
        sc.get("needs_deeper_research", False)
        for sc in state.get("sub_claims", [])
    )

    return "deep_research" if needs_more else "proceed"


def build_graph() -> StateGraph:
    graph = StateGraph(FactCheckerState)

    # Add all nodes
    graph.add_node("deconstructor",    deconstructor_node)
    graph.add_node("researcher",       researcher_node)
    graph.add_node("evaluator",        evaluator_node)
    graph.add_node("deep_researcher",  deep_researcher_node)
    graph.add_node("fallacy_detector", fallacy_detector_node)
    graph.add_node("writer",           writer_node)

    # Entry point
    graph.set_entry_point("deconstructor")

    # Linear edges: deconstruct → research → evaluate
    graph.add_edge("deconstructor", "researcher")
    graph.add_edge("researcher",    "evaluator")

    # Conditional edge: after evaluation, either dig deeper or proceed
    graph.add_conditional_edges(
        "evaluator",
        should_dig_deeper,
        {
            "deep_research": "deep_researcher",
            "proceed":       "fallacy_detector",
        }
    )

    # Deep research loops back to evaluator for re-assessment
    graph.add_edge("deep_researcher", "evaluator")

    # After fallacy detection, write the report
    graph.add_edge("fallacy_detector", "writer")
    graph.add_edge("writer",           END)

    return graph.compile()


# Module-level compiled graph for import
fact_checker_graph = build_graph()
