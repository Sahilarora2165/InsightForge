.PHONY: help dev up down build test lint format clean db-reset logs

# Default target
help:
	@echo "InternalKnowledgeHub - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make up           - Start all services with docker-compose"
	@echo "  make down         - Stop all services"
	@echo "  make build        - Build all Docker images"
	@echo "  make logs         - View logs from all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests only"
	@echo "  make test-frontend- Run frontend tests only"
	@echo "  make coverage     - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-reset     - Reset database"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean up generated files"
	@echo "  make shell-backend- Open shell in backend container"
	@echo "  make pull-models  - Pull Ollama models"

# Development
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@echo ""
	@echo "Services are starting up!"
	@echo "  Frontend: http://localhost:80"
	@echo "  API:      http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Ollama:   http://localhost:11434"

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

# Testing
test: test-backend test-frontend

test-backend:
	docker-compose exec backend pytest tests/ -v

test-frontend:
	cd frontend && npm test

coverage:
	docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated at backend/htmlcov/index.html"

# Code Quality
lint:
	@echo "Running backend linting..."
	docker-compose exec backend ruff check app/
	@echo "Running frontend linting..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend code..."
	docker-compose exec backend ruff format app/
	@echo "Formatting frontend code..."
	cd frontend && npm run format

# Database
db-migrate:
	docker-compose exec backend flask db upgrade

db-downgrade:
	docker-compose exec backend flask db downgrade

db-reset:
	docker-compose exec backend flask db downgrade base
	docker-compose exec backend flask db upgrade
	docker-compose exec backend python -c "from app.core.init_db import init_db; init_db()"

db-seed:
	docker-compose exec backend python -c "from app.core.init_db import seed_db; seed_db()"

# Utilities
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	rm -rf frontend/coverage 2>/dev/null || true

shell-backend:
	docker-compose exec backend /bin/bash

shell-worker:
	docker-compose exec worker /bin/bash

shell-db:
	docker-compose exec db psql -U postgres -d knowledge_hub

pull-models:
	@echo "Pulling Ollama models..."
	docker-compose exec ollama ollama pull llama3
	docker-compose exec ollama ollama pull nomic-embed-text
	@echo "Models pulled successfully!"

# Production
prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Health checks
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend not responding"
	@curl -s http://localhost:11434/api/tags | jq . || echo "Ollama not responding"
	@echo "Health check complete."

# Initial setup
init:
	cp .env.example .env
	@echo "Environment file created. Please update .env with your settings."
	make build
	make up
	@sleep 10
	make pull-models
	make db-migrate
	make db-seed
	@echo ""
	@echo "Setup complete! Access the application at:"
	@echo "  Frontend: http://localhost:80"
	@echo "  API Docs: http://localhost:8000/docs"
