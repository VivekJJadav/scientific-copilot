from langgraph.graph import StateGraph, END
from app.debate.state import DebateState
from app.debate.agents import proposer_node, critic_node, rebuttal_node, arbiter_node
from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.db.models import HypothesisModel

def should_continue(state: DebateState):
    if len(state["critiques"]) >= settings.DEBATE_MAX_ROUNDS:
        return "arbiter"
    return "critic"

def build_debate_graph():
    workflow = StateGraph(DebateState)
    
    workflow.add_node("proposer", proposer_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("rebuttal", rebuttal_node)
    workflow.add_node("arbiter", arbiter_node)
    
    workflow.set_entry_point("proposer")
    
    workflow.add_edge("proposer", "critic")
    workflow.add_edge("critic", "rebuttal")
    
    workflow.add_conditional_edges("rebuttal", should_continue)
    
    workflow.add_edge("arbiter", END)
    
    return workflow.compile()

async def run_debate(
    hypothesis: HypothesisModel,
    source_papers: list[ResearchAtom],
    debate_history: str = "",
) -> DebateState:
    graph = build_debate_graph()
    
    initial_state: DebateState = {
        "hypothesis_id": str(hypothesis.id) if hasattr(hypothesis, "id") and hypothesis.id else "unknown",
        "hypothesis": hypothesis,
        "source_papers": source_papers,
        "proposal": "",
        "critiques": [],
        "rebuttals": [],
        "round": 0,
        "arbiter_verdict": None,
        "final_hypothesis": None,
        "rejection_reason": None,
        "debate_history": debate_history,
    }
    
    # LangGraph returns the final state
    final_state = await graph.ainvoke(initial_state)
    return final_state
