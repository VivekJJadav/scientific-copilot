from langgraph.graph import StateGraph, END
from app.debate.state import DebateState
from app.debate.agents import proposer_node, critic_node, rebuttal_node, arbiter_node
from app.config.settings import settings
from app.core.atoms import ResearchAtom
from app.reasoning.hypothesis import Hypothesis

def should_continue(state: DebateState):
    # Proposer increments to 1. 
    # Rebuttal increments state["round"] at the end of its cycle.
    # We want exactly DEBATE_MAX_ROUNDS of critic-rebuttal pairs.
    # Since round starts at 0, proposer->1.
    # round 1: critic -> rebuttal (increments to 2)
    # round 2: critic -> rebuttal (increments to 3)
    # round 3: critic -> rebuttal (increments to 4)
    # Wait, the user specifically noted DEBATE_MAX_ROUNDS (default 3). 
    # If state["round"] is > DEBATE_MAX_ROUNDS, we go to arbiter.
    if state["round"] > settings.DEBATE_MAX_ROUNDS:
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

async def run_debate(hypothesis: Hypothesis, source_papers: list[ResearchAtom]) -> DebateState:
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
        "rejection_reason": None
    }
    
    # LangGraph returns the final state
    final_state = await graph.ainvoke(initial_state)
    return final_state
