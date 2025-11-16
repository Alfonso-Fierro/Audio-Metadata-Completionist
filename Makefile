.PHONY: help install install-dev test format lint type-check clean run

help:
	@echo "Audio Metadata Completionist - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make test          Run test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make format        Format code with black and isort"
	@echo "  make lint          Run linting with pylint"
	@echo "  make type-check    Run type checking with mypy"
	@echo "  make clean         Clean cache and build files"
	@echo "  make all-checks    Run all quality checks"
	@echo "  make run           Run the CLI"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest -v

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/
	@echo "Code formatted successfully!"

lint:
	pylint src/

type-check:
	mypy src/

all-checks: format type-check test
	@echo "All checks passed!"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ dist/ build/
	rm -rf .cache/ logs/*.log
	@echo "Cleaned up cache and build files!"

run:
	python main.py --help
