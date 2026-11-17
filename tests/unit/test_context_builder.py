import pytest
from local_ai.application.context_builder import ContextBuilder


@pytest.mark.asyncio
async def test_history_trimmed():
    b = ContextBuilder(max_history_turns=2)
    hist = [{"role": "user", "content": f"m{i}"} for i in range(10)]
    ctx = await b.build("now", hist, "sys")
    assert len(ctx.history) == 2