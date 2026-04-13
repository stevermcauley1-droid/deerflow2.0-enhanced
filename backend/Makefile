install:
	uv sync

dev:
	uv run langgraph dev --no-browser --allow-blocking --no-reload

gateway:
	PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001

test:
	PYTHONPATH=. uv run pytest tests/ -v

test-jobs2go:
	PYTHONPATH=. uv run pytest tests/test_jobs2go_pilot_services.py -v

gate-jobs2go:
	uvx ruff check app/gateway/routers/jobs2go_*.py tests/test_jobs2go_pilot_services.py
	PYTHONPATH=. uv run pytest tests/test_jobs2go_pilot_services.py -v

lint:
	uvx ruff check .

format:
	uvx ruff check . --fix && uvx ruff format .
