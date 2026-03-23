"""All prompt templates for the LLM extraction and reasoning pipeline.

Every prompt used in the system lives here — do not scatter prompts across files.
"""

EXTRACTION_PROMPT = """From this abstract extract:
1. Core methods used (list of short method names, e.g. "PPO", "LoRA", "RLHF")
2. Limitations stated by the authors (direct quotes or close paraphrases)
3. Key empirical claims made (what the paper claims to show)

Abstract: {abstract}

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
