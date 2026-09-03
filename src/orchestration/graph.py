from langgraph.graph import StateGraph, START, END
from src.domain.enums import Decision
from src.orchestration.state import MapQAState
from src.orchestration.nodes import (
    ingest_and_index_node,
    process_qa_and_policy_node,
    llm_advisory_node,
    finalize_report_node,
    persist_to_db_node
)

def route_after_policy(state: MapQAState) -> str:
    # If any document requires human review, route to LLM advisory first
    if state.get("human_review_queue") and len(state["human_review_queue"]) > 0:
        return "llm_advisory_node"
    return "finalize_report_node"

def build_map_qa_graph():
    builder = StateGraph(MapQAState)
    
    builder.add_node("ingest_and_index_node", ingest_and_index_node)
    builder.add_node("process_qa_and_policy_node", process_qa_and_policy_node)
    builder.add_node("llm_advisory_node", llm_advisory_node)
    builder.add_node("finalize_report_node", finalize_report_node)
    builder.add_node("persist_to_db_node", persist_to_db_node)
    
    builder.add_edge(START, "ingest_and_index_node")
    builder.add_edge("ingest_and_index_node", "process_qa_and_policy_node")
    
    builder.add_conditional_edges(
        "process_qa_and_policy_node",
        route_after_policy,
        {
            "llm_advisory_node": "llm_advisory_node",
            "finalize_report_node": "finalize_report_node"
        }
    )
    
    builder.add_edge("llm_advisory_node", "finalize_report_node")
    builder.add_edge("finalize_report_node", "persist_to_db_node")
    builder.add_edge("persist_to_db_node", END)
    
    return builder.compile()

map_qa_workflow = build_map_qa_graph()

