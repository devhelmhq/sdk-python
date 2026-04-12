.PHONY: build test lint lint-fix typecheck typegen clean release help

build:  ## Build the package
	uv run python -m build

test:  ## Run unit tests
	uv run pytest

lint:  ## Run ruff linter + formatter check
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

lint-fix:  ## Auto-fix lint and format issues
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck:  ## Run mypy strict type checking
	uv run mypy src/

typegen:  ## Regenerate Pydantic models from OpenAPI spec
	./scripts/typegen.sh

clean:  ## Remove build artifacts
	rm -rf dist build *.egg-info src/*.egg-info

release:  ## Release a new version: make release VERSION=0.1.0
	@test -n "$(VERSION)" || (echo "Usage: make release VERSION=x.y.z" && exit 1)
	./scripts/release.sh $(VERSION)

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
