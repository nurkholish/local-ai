import asyncio
import ipaddress
import logging
import re
import socket
import time
from functools import wraps
from urllib.parse import urlparse

from local_ai.infrastructure.observability.tool_metrics import TOOL_DURATION, TOOL_ERRORS

log = logging.getLogger(__name__)

MAX_OUTPUT = 4000
TIMEOUT = 15


def tool_safe(name: str):
    def decorator(fn):
        @wraps(fn)
        async def _wrapped(*args, **kwargs):
            start = time.time()
            try:
                result = await asyncio.wait_for(fn(*args, **kwargs), timeout=TIMEOUT)
                TOOL_DURATION.labels(tool=name).observe(time.time() - start)
                return str(result)[:MAX_OUTPUT]
            except asyncio.TimeoutError:
                TOOL_ERRORS.labels(tool=name, error_type="timeout").inc()
                log.warning("tool %s timeout", name)
                return f"[tool:{name} timeout after {TIMEOUT}s]"
            except ValueError as e:
                TOOL_ERRORS.labels(tool=name, error_type="value_error").inc()
                log.warning("tool %s value error: %s", name, e)
                return f"[tool:{name} invalid input: {e}]"
            except Exception as e:
                TOOL_ERRORS.labels(tool=name, error_type=type(e).__name__).inc()
                log.exception("tool %s failed", name)
                return f"[tool:{name} error:{type(e).__name__}]"
        return _wrapped
    return decorator


def _strip_html(text: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@tool_safe("search_web")
async def search_web(query: str) -> str:
    import httpx
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0"}

    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as c:
            r = await c.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 3},
            )
            if r.status_code == 200:
                hits = r.json().get("query", {}).get("search", [])
                if hits:
                    snippets = [_strip_html(h.get("snippet", "")) for h in hits[:3]]
                    result = " | ".join(s for s in snippets if s)
                    if result:
                        return result[:800]
    except Exception as e:
        log.warning("wiki failed: %s", type(e).__name__)

    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as c:
            r = await c.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1"},
            )
            if r.status_code == 200:
                abstract = (r.json().get("AbstractText") or "").strip()
                if abstract:
                    return abstract[:800]
    except Exception as e:
        log.warning("ddg failed: %s", type(e).__name__)

    return f"[search unavailable for '{query[:50]}']"


@tool_safe("calculator")
async def calculator(expression: str) -> str:
    from simpleeval import simple_eval
    try:
        return str(simple_eval(expression))
    except Exception as e:
        raise ValueError(f"cannot evaluate '{expression[:50]}'") from e


@tool_safe("fetch_url")
async def fetch_url(url: str) -> str:
    p = urlparse(url)
    if p.scheme != "https":
        raise ValueError("only https URLs allowed")
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(p.hostname))
        if ip.is_private or ip.is_loopback:
            raise ValueError("private IP blocked")
    except (socket.gaierror, ValueError) as e:
        if "blocked" in str(e):
            raise
        raise ValueError("unresolvable host") from e

    import httpx
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(url, follow_redirects=False)
        return r.text[:MAX_OUTPUT]


TOOL_IMPL = {"search_web": search_web, "calculator": calculator, "fetch_url": fetch_url}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "search_web", "description": "Search web for factual information",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "calculator", "description": "Evaluate a math expression",
        "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "fetch_url", "description": "Fetch an https URL content",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]