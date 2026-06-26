.PHONY: dev worker beat migrate makemigrations seed test lint format docker-up docker-down

dev:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A backend.workers.celery_app worker --loglevel=info --concurrency=4

beat:
	celery -A backend.workers.celery_app beat --loglevel=info

migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate -m "$(message)"

downgrade:
	alembic downgrade -1

seed:
	python -m backend.scripts.seed

test:
	pytest backend/tests/ -v --cov=backend --cov-report=html --cov-report=term-missing

test-fast:
	pytest backend/tests/ -v -x

lint:
	ruff check backend/
	mypy backend/

format:
	ruff format backend/
	ruff check --fix backend/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-reset:
	docker-compose down -v && docker-compose up -d

docker-logs:
	docker-compose logs -f api

shell:
	python -c "import asyncio; from backend.database import AsyncSessionLocal; print('DB ready')"
