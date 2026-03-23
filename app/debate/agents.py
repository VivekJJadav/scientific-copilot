import time
import json
import structlog
from app.debate.state import DebateState
from app.llm.router import LLMRouter
from app.llm.prompts import PROPOSER_PROMPT, CRITIC_PROMPT, REBUTTAL_PROMPT, ARBITER_PROMPT
from app.config.settings import settings

logger = structlog.get_logger(__name__)

def _format_papers(papers) -> str:
    return "\n\n".join([
        f"Title: {p.title}\nMethods: {p.methods}\nClaims: {p.claims}" 
        for p in papers
    ])

async def proposer_node(state: DebateState) -> DebateState:
    start_time = time.monotonic()
    llm = LLMRouter()
    
    hypothesis = state["hypothesis"]
    
    formatted_critiques = "\n".join(state.get("critiques", []))
    prompt = PROPOSER_PROMPT.format(
        hypothesis_title=hypothesis.title,
        core_claim=hypothesis.core_claim,
        method_sketch=hypothesis.method_sketch,
        paper_summaries=_format_papers(state["source_papers"]),
        critiques=formatted_critiques if formatted_critiques else "None yet",
        hardware_requirement=hypothesis.hardware_requirement
    )
    
    response = await llm.complete(prompt)
    
    state["proposal"] = response
    state["round"] = state.get("round", 0) + 1
    
    logger.info(
        "debate_node_executed",
        agent="proposer",
        round=state["round"],
        latency=time.monotonic() - start_time,
        hypothesis_id=state["hypothesis_id"]
    )
    return state


async def critic_node(state: DebateState) -> DebateState:
    start_time = time.monotonic()
    llm = LLMRouter()
    
    hypothesis = state["hypothesis"]
    
    prompt = CRITIC_PROMPT.format(
        hypothesis_title=hypothesis.title,
        core_claim=hypothesis.core_claim,
        method_sketch=hypothesis.method_sketch,
        proposal=state["proposal"],
        paper_summaries=_format_papers(state["source_papers"]),
        hardware_requirement=hypothesis.hardware_requirement
    )
    
    response = await llm.complete(prompt)
    
    critiques = state.get("critiques", [])
    critiques.append(response)
    state["critiques"] = critiques
    
    logger.info(
        "debate_node_executed",
        agent="critic",
        round=state["round"],
        latency=time.monotonic() - start_time,
        hypothesis_id=state["hypothesis_id"]
    )
    return state


async def rebuttal_node(state: DebateState) -> DebateState:
    start_time = time.monotonic()
    llm = LLMRouter()
    
    hypothesis = state["hypothesis"]
    latest_critique = state["critiques"][-1]
    
    prompt = REBUTTAL_PROMPT.format(
        hypothesis_title=hypothesis.title,
        core_claim=hypothesis.core_claim,
        latest_critique=latest_critique
    )
    
    response = await llm.complete(prompt)
    
    rebuttals = state.get("rebuttals", [])
    rebuttals.append(response)
    state["rebuttals"] = rebuttals
    
    # Increment round in rebuttal as well to progress the cycle
    state["round"] += 1
    
    logger.info(
        "debate_node_executed",
        agent="rebuttal",
        round=state["round"] - 1, # log the round we were just in
        latency=time.monotonic() - start_time,
        hypothesis_id=state["hypothesis_id"]
    )
    return state


async def arbiter_node(state: DebateState) -> DebateState:
    start_time = time.monotonic()
    llm = LLMRouter()
    
    hypothesis = state["hypothesis"]
    
    prompt = ARBITER_PROMPT.format(
        hypothesis_title=hypothesis.title,
        core_claim=hypothesis.core_claim,
        novelty_score=hypothesis.novelty_score,
        feasibility_score=hypothesis.feasibility_score,
        proposal=state["proposal"],
        critiques="\n\n".join(state.get("critiques", [])),
        rebuttals="\n\n".join(state.get("rebuttals", [])),
        hardware_requirement=hypothesis.hardware_requirement
    )
    
    response = await llm.complete(prompt, expect_json=True, force_json_object=True)
    
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        # Fallback if invalid JSON
        parsed = {
            "verdict": "FAIL",
            "final_novelty_score": getattr(hypothesis, "novelty_score", 0.0),
            "final_feasibility_score": getattr(hypothesis, "feasibility_score", 0.0),
            "surviving_risks": [],
            "rejection_reason": "Arbiter returned invalid JSON format.",
            "arbiter_notes": "JSON parsing error."
        }
        
    verdict = parsed.get("verdict", "FAIL")
    state["arbiter_verdict"] = verdict
    
    # Needs to be a new object or we update in place depending on architecture. 
    # State has `final_hypothesis` and `rejection_reason`.
    if verdict == "PASS":
        hypothesis.novelty_score = float(parsed.get("final_novelty_score", hypothesis.novelty_score))
        hypothesis.feasibility_score = float(parsed.get("final_feasibility_score", hypothesis.feasibility_score))
        
        # Merge new risks with existing risks to be safe
        existing_risks = hypothesis.risk_factors or []
        new_risks = parsed.get("surviving_risks", [])
        hypothesis.risk_factors = list(set(existing_risks + new_risks))
        
        state["final_hypothesis"] = hypothesis
        state["rejection_reason"] = None
    else:
        state["final_hypothesis"] = None
        state["rejection_reason"] = parsed.get("rejection_reason", "No reason provided by Arbiter.")
        
    # arbiter notes can be saved to the object
    hypothesis.arbiter_notes = parsed.get("arbiter_notes", "")
        
    logger.info(
        "debate_node_executed",
        agent="arbiter",
        round=state["round"],
        latency=time.monotonic() - start_time,
        hypothesis_id=state["hypothesis_id"],
        verdict=verdict
    )
    
    return state
