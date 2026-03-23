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
