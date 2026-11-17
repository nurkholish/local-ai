from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "local-ai"
    env: str = "local"
    log_level: str = "INFO"
    log_json: bool = True
    port: int = 8080

    # Routing
    llm_route_mode: str = "hybrid"
    llm_max_retries: int = 2
    llm_timeout_s: int = 30
    llm_route_classifier_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    llm_route_local_model: str = "Qwen/Qwen2.5-7B-Instruct-AWQ"
    llm_route_frontier_model: str = "gpt-4o-mini"

    # LLM performance
    llm_max_output_tokens: int = 512
    llm_cache_prompt: bool = True
    llm_early_return_calculator: bool = True
    llm_streaming_enabled: bool = True
    llm_fallback_enabled: bool = True

    # Circuit breaker + retry
    cb_failure_threshold: int = 5
    cb_recovery_timeout_s: float = 30.0
    retry_budget_s: float = 120.0
    retry_max_attempts: int = 3

    # PII + dedup
    pii_redaction_enabled: bool = True
    pii_redaction_on_output: bool = True
    dedup_enabled: bool = True

    openai_api_key: str | None = None

    # Local
    vllm_enabled: bool = False
    vllm_router_url: str = "http://vllm-router:8001/v1"
    vllm_main_url: str = "http://vllm-main:8002/v1"
    embedding_url: str = "http://embedding:8003"

    # Infra
    redis_url: str = "redis://redis:6379/0"
    database_url: str = "postgresql+asyncpg://agent:agent@postgres:5432/agent"

    # Limits
    max_agent_steps: int = 8
    max_tool_output_chars: int = 4000
    tool_timeout_s: int = 15
    rate_limit_per_min: int = 60
    max_history_turns: int = 10
    max_rag_chunks: int = 5

    # Observability
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://otel-collector:4317"
    otel_service_name: str = "local-ai-api"
    prometheus_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()