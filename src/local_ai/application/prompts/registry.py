import logging
from pathlib import Path

import yaml

log = logging.getLogger(__name__)


class PromptRegistry:
    def __init__(self, path: str = "src/local_ai/application/prompts/templates.yaml"):
        self._path = Path(path)
        self._data: dict = {}
        self.reload()

    def reload(self) -> None:
        try:
            with open(self._path) as f:
                self._data = yaml.safe_load(f) or {}
            log.info("prompts reloaded: %d categories", len(self._data))
        except Exception:
            log.exception("prompt reload failed")
            self._data = {}

    def get(self, category: str, name: str, **kwargs) -> str:
        try:
            template = self._data[category][name]["content"]
            return template.format(**kwargs) if kwargs else template
        except (KeyError, AttributeError):
            log.error("prompt not found: %s.%s", category, name)
            return "You are a helpful AI assistant."


_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry