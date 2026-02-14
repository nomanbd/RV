.PHONY: up down backend frontend migrate seed test lint

up:
	docker compose up -d

down:
	docker compose down

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed:
	cd backend && python -m scripts.seed_data

test:
	cd backend && pytest tests/ -v

test-cov:
	cd backend && pytest tests/ -v --cov=app --cov-report=html

lint:
	cd backend && ruff check app/ && ruff format --check app/

format:
	cd backend && ruff format app/

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install
