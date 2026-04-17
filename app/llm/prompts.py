"""All prompt templates for the LLM extraction and reasoning pipeline.

Every prompt used in the system lives here — do not scatter prompts across files.
"""

EXTRACTION_PROMPT = """From this paper text extract:
1. Core methods used (list of short method names, e.g. "PPO", "LoRA", "RLHF")
2. Limitations stated by the authors (direct quotes or close paraphrases)
3. Key empirical claims made (what the paper claims to show)

Paper text: {abstract}

Respond in JSON only. No preamble. Format:
{{
  "methods": ["...", "..."],
  "limitations": ["...", "..."],
  "claims": ["...", "..."]
}}"""

GAP_EXTRACTION_PROMPT = """You are a research analyst. Below are limitations and future work statements from {n} paper(s) on the topic "{topic}".

{limitations_block}

Identify the top 3 most significant research gaps. A gap is something explicitly unresolved, untested, or flagged as future work in the provided research.

Respond in JSON only. Format:
{{
  "gaps": [
    {{
      "description": "...",
      "source_paper_ids": ["...", "..."],
      "gap_type": "untested_combination | missing_benchmark | scalability | generalization"
    }}
  ]
}}"""

HYPOTHESIS_GENERATION_PROMPT = """You are a research scientist. Given the following research gap and the papers that identified it, generate a concrete, testable hypothesis.

Gap: {gap_description}
Source papers: {paper_summaries}
Hardware constraint: {max_compute}

Generate a hypothesis that a solo developer could test on {max_compute}.

Respond in JSON only. Format:
{{
  "title": "...",
  "motivation": "...",
  "core_claim": "...",
  "method_sketch": "...",
  "expected_outcome": "...",
  "risk_factors": ["...", "..."],
  "novelty_score": 0.0,
  "feasibility_score": 0.0,
  "hardware_requirement": "..."
}}"""

NOVELTY_CHECK_PROMPT = """You are a research reviewer. Given this new hypothesis and a list of existing hypotheses, score how novel the new one is.

New hypothesis: {hypothesis_title} — {core_claim}

Existing hypotheses:
{existing_titles}

Novelty score rules:
- 1.0: completely new idea, no overlap with existing
- 0.6-0.9: related but meaningfully different angle
- 0.3-0.5: similar to existing work, minor variation
- 0.0-0.2: essentially the same as an existing hypothesis

Respond in JSON only: {{"novelty_score": 0.0, "reasoning": "..."}}"""

PROPOSER_PROMPT = """You are an optimistic research scientist. Given the following hypothesis and the papers that grounded it, make the strongest possible case for why this research direction is worth pursuing.

Hypothesis: {hypothesis_title}
Core claim: {core_claim}
Method sketch: {method_sketch}
Source papers summary: {paper_summaries}
Critic's objections (if any): {critiques}

Argue specifically for:
1. Why this gap is real and significant
2. Why the method sketch is sound
3. Why this is achievable on {hardware_requirement}

Respond in 3–5 sentences. Be specific, not generic."""

CRITIC_PROMPT = """You are a skeptical senior researcher reviewing a hypothesis. Your job is to find every reason this idea won't work, isn't novel, or can't be tested by a solo developer.

Hypothesis: {hypothesis_title}
Core claim: {core_claim}
Method sketch: {method_sketch}
Proposer's argument: {proposal}
Source papers: {paper_summaries}

Challenge specifically:
1. Is this claim already shown in existing literature?
2. Does the method sketch actually test the core claim?
3. Can this realistically run on {hardware_requirement}?
4. What would make this experiment fail silently?

Respond in 3–5 sentences. Be specific and harsh."""

REBUTTAL_PROMPT = """You are the original researcher defending your hypothesis against criticism.

Your hypothesis: {hypothesis_title}
Core claim: {core_claim}
Critic's objection: {latest_critique}

Respond to each objection specifically. If the critic has a valid point, acknowledge it and explain how you would address it. Do not dismiss objections without reasoning.

Respond in 3–5 sentences."""

ARBITER_PROMPT = """You are a senior research editor evaluating a hypothesis debate. Review the full exchange and produce a final verdict.

Hypothesis: {hypothesis_title}
Core claim: {core_claim}
Original novelty score: {novelty_score}
Original feasibility score: {feasibility_score}

Debate summary:
Proposal: {proposal}
Critiques: {critiques}
Rebuttals: {rebuttals}

Evaluate:
1. Did the core claim survive the critique?
2. Did the method sketch hold up?
3. Were the Critic's objections adequately addressed?
4. Is this still feasible on {hardware_requirement}?

Respond in JSON only:
{{
  "verdict": "PASS" | "FAIL",
  "final_novelty_score": 0.0,
  "final_feasibility_score": 0.0,
  "surviving_risks": ["...", "..."],
  "rejection_reason": "..." | null,
  "arbiter_notes": "..."
}}"""

# ─── Phase 4 Prompts ───────────────────────────────────────────────────────────

RESULT_ANALYSIS_PROMPT = """You are a research analyst reviewing the results of a machine learning experiment.

Hypothesis tested: {hypothesis_title}
Core claim: {core_claim}
Expected outcome: {expected_outcome}
Actual results: {results}

Determine:
1. Outcome: did the results validate, fail to support, or inconclusively test the core claim?
2. Lessons learned: what specific insights does this result provide for future research?
3. If failed: what was the most likely reason for failure?

Respond in JSON only:
{{
  "outcome": "validated" | "failed" | "inconclusive",
  "result_summary": "...",
  "lessons_learned": ["...", "..."],
  "failure_reason": "..." | null
}}"""

NEGATIVE_RESULT_GAP_PROMPT = """You are a research scientist. An experiment just failed with the following findings:

Hypothesis: {hypothesis_title}
Core claim: {core_claim}
Failure reason: {failure_reason}
Lessons learned: {lessons_learned}

A failed experiment is valuable data. Based on this failure, identify one new research gap it reveals — something that could be tested differently or under different conditions to understand why it failed.

Respond in JSON only:
{{
  "gap_description": "...",
  "gap_type": "untested_combination | missing_benchmark | scalability | generalization | negative_result",
  "suggested_direction": "..."
}}"""

DATASET_EXTRACTION_PROMPT = """You are a research data analyst. From the following paper abstract and methods, extract the names of any datasets or benchmarks used or referenced.

Title: {title}
Abstract: {abstract}
Methods: {methods}

Return only dataset and benchmark names that are proper nouns — named datasets like "Atari", "MuJoCo", "GLUE", "ImageNet", "OpenAI Gym", "D4RL". Do not include generic terms like "training data" or "test set".

Respond in JSON only:
{{
  "datasets": ["...", "..."]
}}"""

ARBITER_FEW_SHOT_PREFIX = """Before evaluating this debate, here are examples of past hypotheses and their experimental outcomes to calibrate your scoring:

{few_shot_examples}

Use these examples to inform your scoring — hypotheses similar to validated ones should score higher on feasibility, hypotheses similar to failed ones should have their risk factors weighted more heavily.

"""


def build_arbiter_prompt_with_examples(
    hypothesis_title: str,
    core_claim: str,
    novelty_score: float,
    feasibility_score: float,
    proposal: str,
    critiques: list[str],
    rebuttals: list[str],
    hardware_requirement: str,
    few_shot_examples: list[dict],
) -> str:
    """Build the full Arbiter prompt, prepending few-shot prefix only when examples exist."""
    prefix = ""
    if few_shot_examples:
        examples_block = ""
        for ex in few_shot_examples:
            examples_block += (
                f"- Title: {ex.get('hypothesis_title', 'N/A')}\n"
                f"  Claim: {ex.get('core_claim', 'N/A')}\n"
                f"  Outcome: {ex.get('outcome', 'N/A')}\n"
                f"  Summary: {ex.get('result_summary', 'N/A')}\n\n"
            )
        prefix = ARBITER_FEW_SHOT_PREFIX.format(few_shot_examples=examples_block)

    base = ARBITER_PROMPT.format(
        hypothesis_title=hypothesis_title,
        core_claim=core_claim,
        novelty_score=novelty_score,
        feasibility_score=feasibility_score,
        proposal=proposal,
        critiques="\n\n".join(critiques),
        rebuttals="\n\n".join(rebuttals),
        hardware_requirement=hardware_requirement,
    )
    return prefix + base
