import time
import structlog
from pydantic import BaseModel, Field, ValidationError
from app.debate.state import DebateState
from app.llm.router import LLMRouter
from app.llm.prompts import PROPOSER_PROMPT, CRITIC_PROMPT, REBUTTAL_PROMPT, ARBITER_PROMPT, build_arbiter_prompt_with_examples
from app.config.settings import settings

logger = structlog.get_logger(__name__)


class ArbiterResponseSchema(BaseModel):
    verdict: str = "FAIL"
    final_novelty_score: float = 0.0
    final_feasibility_score: float = 0.0
    surviving_risks: list[str] = Field(default_factory=list)
    rejection_reason: str = "No reason provided by Arbiter."
    arbiter_notes: str = ""
    key_objections: list[str] = Field(default_factory=list)
    addressed_prior_objections: list[str] = Field(default_factory=list)

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
    state["round"] = 0
    
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
    
    # We are in round N
    current_round = len(critiques)
    state["round"] = current_round
    
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
    
    logger.info(
        "debate_node_executed",
        agent="rebuttal",
        round=state["round"],
        latency=time.monotonic() - start_time,
        hypothesis_id=state["hypothesis_id"]
    )
    return state


async def arbiter_node(state: DebateState) -> DebateState:
    start_time = time.monotonic()
    llm = LLMRouter()
    
    hypothesis = state["hypothesis"]
    
    # Load few-shot examples from past outcomes for Arbiter calibration
    from app.feedback.arbiter_trainer import ArbiterTrainer
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.db.session import engine
    from app.db.models import DebateHistory
    
    few_shot_examples = []
    try:
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as db:
            trainer = ArbiterTrainer()
            few_shot_examples = await trainer.get_few_shot_examples(db)
    except Exception as e:
        logger.warning("arbiter_few_shot_load_failed", error=str(e))
    
    # Get ancestor debate history (already formatted by run_debate)
    debate_history = state.get("debate_history", "")
    
    # Build prompt with history, few-shot examples, and current debate
    prompt = build_arbiter_prompt_with_examples(
        hypothesis_title=hypothesis.title,
        core_claim=hypothesis.core_claim,
        novelty_score=hypothesis.novelty_score,
        feasibility_score=hypothesis.feasibility_score,
        proposal=state["proposal"],
        critiques=state.get("critiques", []),
        rebuttals=state.get("rebuttals", []),
        hardware_requirement=hypothesis.hardware_requirement,
        few_shot_examples=few_shot_examples,
        debate_history=debate_history,
    )
    
    response = await llm.complete(prompt, expect_json=True, force_json_object=True)
    
    try:
        parsed = ArbiterResponseSchema.model_validate_json(response)
    except ValidationError as e:
        logger.warning(
            "arbiter_validation_failed",
            error=str(e),
            raw_output=response,
            hypothesis_id=state["hypothesis_id"],
        )
        # Fallback if invalid JSON
        parsed = ArbiterResponseSchema(
            verdict="FAIL",
            final_novelty_score=getattr(hypothesis, "novelty_score", 0.0),
            final_feasibility_score=getattr(hypothesis, "feasibility_score", 0.0),
            surviving_risks=[],
            rejection_reason="Arbiter returned invalid JSON format.",
            arbiter_notes="JSON parsing error.",
        )
        
    verdict = parsed.verdict
    state["arbiter_verdict"] = verdict
    
    if verdict == "PASS":
        hypothesis.novelty_score = float(parsed.final_novelty_score or hypothesis.novelty_score)
        hypothesis.feasibility_score = float(parsed.final_feasibility_score or hypothesis.feasibility_score)
        
        # Merge new risks with existing risks to be safe
        existing_risks = hypothesis.risk_factors or []
        new_risks = parsed.surviving_risks
        hypothesis.risk_factors = list(set(existing_risks + new_risks))
        
        state["final_hypothesis"] = hypothesis
        state["rejection_reason"] = None
    else:
        state["final_hypothesis"] = None
        state["rejection_reason"] = parsed.rejection_reason
        
    # Arbiter notes and structured objections saved to state for persistence
    hypothesis.arbiter_notes = parsed.arbiter_notes
    state["_arbiter_parsed"] = parsed.model_dump()
        
    logger.info(
        "debate_node_executed",
        agent="arbiter",
        round=state["round"],
        latency=time.monotonic() - start_time,
        hypothesis_id=state["hypothesis_id"],
        verdict=verdict,
        few_shot_count=len(few_shot_examples),
        has_debate_history=bool(debate_history),
        key_objections_count=len(parsed.key_objections),
        addressed_prior_count=len(parsed.addressed_prior_objections),
    )
    
    return state
