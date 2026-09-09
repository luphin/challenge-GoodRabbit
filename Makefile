.PHONY: lint types test qa demo

lint:
	.venv/bin/ruff check app tests scripts

types:
	.venv/bin/mypy

test:
	.venv/bin/pytest --cov

qa: lint types test

demo:
	docker compose down -v
	docker compose up --build -d
	@until docker compose exec -T api curl -sf http://localhost:8000/health > /dev/null 2>&1; do sleep 2; done
	docker compose exec api python scripts/seed.py
	bash scripts/demo.sh
