import os
import pytest

os.environ.setdefault("ENV", "test")
os.environ.setdefault("OTEL_ENABLED", "false")
os.environ.setdefault("LOG_JSON", "false")