import asyncio
from app.feedback.arbiter_trainer import ArbiterTrainer
from app.llm.prompts import build_arbiter_prompt_with_examples

async def test():
    trainer = ArbiterTrainer()
    examples = await trainer.get_few_shot_examples(limit=5)
    prompt = build_arbiter_prompt_with_examples(
        "test_title", "test_claim", 0.5, 0.5, "proposal", ["critique1"], ["rebuttal1"], "GPU", examples
    )
    print("Found examples:", len(examples))
    print("Prompt inclusion:", "Here are some examples of past decisions" in prompt)

asyncio.run(test())
