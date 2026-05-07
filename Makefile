.PHONY: help install dev migrate seed test lint typecheck e2e build clean api-shell web-shell docker-up docker-down bench bench-regress

help:
	@echo "Targets:"
	@echo "  install     install api + web dependencies"
	@echo "  dev         run api + web dev servers (requires postgres running)"
	@echo "  migrate     apply Django migrations"
	@echo "  seed        load 12 questions and 30 products into the database"
	@echo "  test        run backend pytest + frontend Vitest"
	@echo "  lint        ruff + eslint + prettier"
	@echo "  typecheck   mypy + tsc --noEmit"
	@echo "  e2e         Playwright cross-browser quiz flow"
	@echo "  build       docker buildx for api and web"
	@echo "  docker-up   docker compose up -d"
	@echo "  docker-down docker compose down -v"
	@echo "  bench       in-process scoring load bench (no server required)"
	@echo "  bench-regress  bench + compare against bench/baselines/baseline-in-process.json"

install:
	cd apps/api && poetry install --no-root
	cd apps/web && pnpm install --frozen-lockfile

migrate:
	cd apps/api && poetry run python manage.py migrate

seed:
	cd apps/api && poetry run python manage.py seed_catalog
	cd apps/api && poetry run python manage.py seed_variants

dev:
	@echo "Run 'make docker-up' for postgres, then in two shells:"
	@echo "  cd apps/api && poetry run python manage.py runserver"
	@echo "  cd apps/web && pnpm dev"

test:
	cd apps/api && poetry run pytest
	cd apps/web && pnpm test -- --run

lint:
	cd apps/api && poetry run ruff check .
	cd apps/web && pnpm lint
	cd apps/web && pnpm format:check

typecheck:
	cd apps/api && poetry run mypy apps config
	cd apps/web && pnpm typecheck

e2e:
	cd apps/web && pnpm exec playwright install --with-deps && pnpm exec playwright test

build:
	docker buildx build -t recommendation-quiz-api:local apps/api
	docker buildx build -t recommendation-quiz-web:local apps/web

docker-up:
	docker compose up -d

docker-down:
	docker compose down -v

clean:
	rm -rf apps/web/node_modules apps/web/dist apps/web/.vite
	rm -rf apps/api/.venv apps/api/.pytest_cache apps/api/.mypy_cache apps/api/.ruff_cache

# Default: 30 second in-process bench. Override via BENCH_DURATION / BENCH_USERS.
BENCH_DURATION ?= 30
BENCH_MAX_ITERS ?= 5000

bench:
	cd apps/api && poetry run python ../../bench/load.py \
		--in-process --duration $(BENCH_DURATION) --max-iters $(BENCH_MAX_ITERS)

bench-regress:
	cd apps/api && poetry run python ../../bench/load.py \
		--in-process --duration $(BENCH_DURATION) --max-iters $(BENCH_MAX_ITERS) \
		--baseline ../../bench/baselines/baseline-in-process.json
