.PHONY: test test-quick test-llm test-chat test-tools test-coverage install-test-deps help

# Default target
help:
	@echo "🧪 Leasing Agent Test Commands"
	@echo "================================"
	@echo "make test          - Run all tests"
	@echo "make test-quick    - Run tests without coverage"
	@echo "make test-llm      - Run LLM service tests only"
	@echo "make test-chat     - Run Chat API tests only"
	@echo "make test-tools    - Run Tools service tests only"
	@echo "make test-coverage - Run tests with coverage report"
	@echo "make install-deps  - Install test dependencies"
	@echo "make clean         - Clean test artifacts"

# Install test dependencies
install-deps:
	poetry install --with test
	poetry add --group test coverage pytest-cov

# Run all tests
test:
	poetry run python run_tests.py

# Quick test run without coverage
test-quick:
	poetry run python -m pytest tests/ -v --tb=short

# Run specific test suites
test-llm:
	poetry run python -m pytest tests/test_llm_service.py -v

test-chat:
	poetry run python -m pytest tests/test_chat_api.py -v

test-tools:
	poetry run python -m pytest tests/test_tools_service.py -v

# Run tests with coverage
test-coverage:
	poetry run python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Watch mode for development
test-watch:
	poetry run python -m pytest tests/ -v --tb=short -f