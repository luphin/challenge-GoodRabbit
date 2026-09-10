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
	@echo "Esperando la API..."
	@i=1; while ! curl -sf --max-time 2 http://localhost:8000/health > /dev/null; do \
		if [ $$i -ge 60 ]; then echo "La API no responde tras 120s"; exit 1; fi; \
		i=$$((i+1)); sleep 2; done
	docker compose exec api python scripts/seed.py
	bash scripts/demo.sh
