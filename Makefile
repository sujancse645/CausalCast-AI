.PHONY: install backend-dev frontend-dev test lint format typecheck build docker-up docker-down
install:
	python -m pip install -r backend/requirements-dev.txt
	cd frontend && npm ci
backend-dev:
	cd backend && python -m uvicorn app.main:app --reload
frontend-dev:
	cd frontend && npm run dev
test:
	cd backend && python -m pytest
	cd frontend && npm test
lint:
	cd backend && python -m ruff check --no-cache .
	cd frontend && npm run lint
format:
	cd backend && python -m ruff format --no-cache .
	cd frontend && npm run format
typecheck:
	cd backend && python -m mypy app
	cd frontend && npm run typecheck
build:
	cd frontend && npm run build
docker-up:
	docker compose up --build
docker-down:
	docker compose down
