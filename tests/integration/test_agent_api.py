import pytest
from httpx import ASGITransport, AsyncClient

from local_ai.interface.http.app import create_app


@pytest.mark.asyncio
async def test_healthz():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/healthz")
        assert r.status_code == 200