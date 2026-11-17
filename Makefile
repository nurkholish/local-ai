.PHONY: help setup env frontend-lock pull build up-local up-prod down logs \
        test test-new eval smoke health clean frontend-rebuild frontend-check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: env frontend-lock pull ## Full first-time setup
	@echo "✅ Setup complete. Run: make up-local"

env: ## Create .env files if missing
	@test -f .env || cp .env.local .env
	@test -f frontend/.env.local || cp frontend/.env.example frontend/.env.local

frontend-lock: ## Generate package-lock.json
	@if [ ! -f frontend/package-lock.json ]; then \
		echo "Generating package-lock.json..."; \
		docker run --rm -v "$(PWD)/frontend:/app" -w /app node:20-alpine \
			npm install --package-lock-only --no-audit --no-fund; \
	fi

pull: ## Pre-pull Docker images
	docker pull kong:3.9.1
	docker pull redis:7-alpine
	docker pull pgvector/pgvector:pg16
	docker pull prom/prometheus:v2.53.0
	docker pull grafana/loki:2.9.8
	docker pull grafana/promtail:2.9.8
	docker pull grafana/tempo:2.5.0
	docker pull grafana/grafana:10.4.5
	docker pull otel/opentelemetry-collector-contrib:0.104.0
	docker pull node:20-alpine
	docker pull nginx:1.27-alpine

build: frontend-lock ## Build all images
	docker compose -f docker-compose.yml -f docker-compose.local.yml build

up-local: env frontend-lock ## Start laptop profile
	docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
	@echo "✅ Stack started. Wait 60s, then: make health && make smoke"

up-prod: env frontend-lock ## Start prod profile
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

down: ## Stop (keep volumes)
	docker compose -f docker-compose.yml -f docker-compose.local.yml down

clean: ## Stop + remove volumes
	docker compose -f docker-compose.yml -f docker-compose.local.yml down -v --remove-orphans

logs: ## Tail all logs
	docker compose logs -f --tail=100

test: ## Run tests
	docker compose cp tests/. api:/app/tests/ 2>/dev/null || true
	docker compose exec api pytest tests/unit tests/integration -v

test-new: ## Test new modules
	docker compose cp tests/. api:/app/tests/ 2>/dev/null || true
	docker compose exec api pytest \
		tests/unit/test_circuit_breaker.py \
		tests/unit/test_pii_redactor.py \
		-v

eval: ## Run eval
	docker compose cp tests/. api:/app/tests/ 2>/dev/null || true
	docker compose exec api python -m tests.eval.eval_harness

smoke: ## Smoke test
	bash scripts/smoke_test.sh

frontend-check: ## TypeScript check
	@docker run --rm -v "$(PWD)/frontend:/app" -w /app node:20-alpine \
		sh -c "npm ci --silent && npx tsc --noEmit"
	@echo "✅ TypeScript OK"

frontend-rebuild: frontend-lock ## Rebuild frontend
	docker compose -f docker-compose.yml -f docker-compose.local.yml build --no-cache frontend
	docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --force-recreate frontend
	@echo "✅ Frontend: http://localhost:3001"

health: ## Full health check
	@echo "=== Containers ==="
	@docker compose ps
	@echo ""
	@echo "=== Ollama ==="
	@curl -s http://localhost:11434/v1/models | head -c 100 || echo "❌ Ollama down"
	@echo ""
	@echo "=== API ==="
	@curl -s http://localhost:8080/healthz || echo "❌ API down"
	@echo ""
	@echo "=== Kong ==="
	@curl -s -H "x-api-key: dev-key" http://localhost:8000/healthz || echo "❌ Kong down"
	@echo ""
	@echo "=== Frontend ==="
	@curl -s http://localhost:3001/api/healthz || echo "❌ Frontend down"
	@echo ""
	@echo "=== Grafana ==="
	@curl -s http://localhost:3000/api/health | head -c 100 || echo "❌ Grafana down"
	@echo ""
	@echo "=== pgvector ==="
	@docker compose exec -T postgres psql -U agent -d agent -tc \
		"SELECT extversion FROM pg_extension WHERE extname='vector';" \
		|| echo "❌ pgvector missing"