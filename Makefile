# Makefile for common deployment tasks

.PHONY: help build up down logs restart clean migrate test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build production Docker image
	docker-compose build

build-dev: ## Build development Docker image
	docker-compose -f docker-compose.dev.yml build

up: ## Start production services
	docker-compose up -d

up-dev: ## Start development services
	docker-compose -f docker-compose.dev.yml up -d

down: ## Stop production services
	docker-compose down

down-dev: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

logs: ## View production logs
	docker-compose logs -f api

logs-dev: ## View development logs
	docker-compose -f docker-compose.dev.yml logs -f api

restart: ## Restart production services
	docker-compose restart

restart-dev: ## Restart development services
	docker-compose -f docker-compose.dev.yml restart

clean: ## Remove containers, volumes, and images
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

migrate: ## Run database migrations (production)
	docker-compose exec api alembic upgrade head

migrate-dev: ## Run database migrations (development)
	docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

migrate-create: ## Create new migration (development)
	docker-compose -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "$(msg)"

test: ## Run tests
	docker-compose -f docker-compose.dev.yml exec api pytest

shell: ## Open shell in production container
	docker-compose exec api /bin/bash

shell-dev: ## Open shell in development container
	docker-compose -f docker-compose.dev.yml exec api /bin/bash

psql: ## Connect to PostgreSQL
	docker-compose exec postgres psql -U sports_user -d sports_analytics

redis-cli: ## Connect to Redis
	docker-compose exec redis redis-cli

health: ## Check service health
	@echo "API Health:"
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"
	@echo "\nPostgreSQL:"
	@docker-compose exec -T postgres pg_isready -U sports_user || echo "PostgreSQL not ready"
	@echo "\nRedis:"
	@docker-compose exec -T redis redis-cli ping || echo "Redis not responding"

backup-db: ## Backup database
	docker-compose exec postgres pg_dump -U sports_user sports_analytics > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore-db: ## Restore database (usage: make restore-db FILE=backup.sql)
	docker-compose exec -T postgres psql -U sports_user sports_analytics < $(FILE)

