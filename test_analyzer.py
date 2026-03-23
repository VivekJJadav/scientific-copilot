import asyncio
from app.feedback.result_analyzer import ResultAnalyzer

async def test():
    analyzer = ResultAnalyzer()
    fake_results = {
        'accuracy': 0.82,
        'loss': 0.34,
        'training_time_seconds': 1200,
        'epochs_completed': 10
    }
    fake_hypothesis = {
        'title': 'Test hypothesis',
        'core_claim': 'Model X outperforms baseline on task Y',
        'expected_outcome': 'accuracy > 0.85'
    }
    analysis = await analyzer.analyze(
        results=fake_results,
        hypothesis=fake_hypothesis,
        experiment_id='test-exp-001'
    )
    print('outcome:', analysis['outcome'])
    print('lessons_learned:', analysis['lessons_learned'])
    print('result_summary:', analysis['result_summary'])

    assert analysis['outcome'] in ['validated', 'failed', 'inconclusive'], \
        f'Invalid outcome value: {analysis["outcome"]}'
    assert isinstance(analysis['lessons_learned'], list), \
        'lessons_learned must be a list'
    assert len(analysis['lessons_learned']) > 0, \
        'lessons_learned must not be empty'
    assert analysis['result_summary'], \
        'result_summary must not be empty'
    print('PASS: result analyzer produces structured output')

asyncio.run(test())
