.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run prek install

.PHONY: gen-all
gen-all: ## Generate all code from schema
	@echo "🚀 Generating all code"
	@uv run scripts/gen_all.py
	@uv run ruff check --fix
	@uv run ruff format .

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit via prek"
	@uv run prek run -a
	@echo "🚀 Static type checking: Running ty"
	@uv run ty check --exclude "src/acp/meta.py" --exclude "src/acp/schema.py" --exclude "examples/*.py"
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry src

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --doctest-modules

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: ## Publish a release to PyPI.
	@echo "🚀 Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve

.PHONY: help
help:
	@awk -F '## ' '/^[A-Za-z_-]+:.*##/ { target = $$1; sub(/:.*/, "", target); printf "\033[36m%-20s\033[0m %s\n", target, $$2 }' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
