.PHONY: build up down backend-test frontend-test lint clean

# Default shell
SHELL := /bin/bash

# Default target
all: build

# Docker build targets
build:
	@echo "Building docker development containers..."
	docker compose build
	@echo "Building docker production containers..."
	docker compose -f docker-compose.prod.yml build

# Docker run targets (dev)
up:
	@echo "Starting development cluster..."
	docker compose up -d

down:
	@echo "Stopping development cluster..."
	docker compose down

# Test runner targets
backend-test:
	@echo "Running backend unit tests..."
	venv/bin/python -m unittest discover tests

frontend-test:
	@echo "Running frontend unit tests..."
	npm --prefix frontend run test

# Linting targets
lint:
	@echo "Running backend syntax compilation lint check..."
	venv/bin/python -m compileall backend/app backend/database tests
	@echo "Running frontend static analysis code check..."
	npm --prefix frontend run lint || true

# Cleanup targets
clean:
	@echo "Cleaning up local workspace temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf frontend/dist frontend/coverage
	@echo "Cleaning up local Docker containers and network volumes..."
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.prod.yml down -v --remove-orphans
