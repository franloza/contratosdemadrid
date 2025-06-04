# Makefile for contratosdemadrid project

# Ensure that commands are executed with bash and that errors cause the script to exit.
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Define the virtual environment directory UV will use
VENV_DIR := venv
# Attempt to find the Python interpreter within the venv for commands
# If the venv doesn't exist yet, this will be empty, but uv venv command will create it.
PYTHON_EXEC := $(VENV_DIR)/bin/python

# Check if uv is installed
UV_INSTALLED := $(shell command -v uv 2> /dev/null)

# Default target (optional)
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install         - Create virtual env and install dependencies using uv."
	@echo "  make extract START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD [DELAY_SECONDS=N] - Run the monthly backfill script using uv."
	@echo "    Example: make extract START_DATE=2025-01-01 END_DATE=2025-03-31 DELAY_SECONDS=5"

.PHONY: check-uv
check-uv:
ifndef UV_INSTALLED
	$(error "uv is not installed or not in PATH. Please install uv: https://github.com/astral-sh/uv")
endif

# Target to create virtual environment and install dependencies
.PHONY: install
install: check-uv
	@echo "Creating/updating virtual environment in $(VENV_DIR) with uv..."
	uv venv $(VENV_DIR) --python $(shell which python3 || echo python3) # Ensure a python3 is found
	@echo "Installing dependencies from pyproject.toml using uv..."
	uv pip sync pyproject.toml --python $(PYTHON_EXEC)
	@echo "Installing Playwright browser binaries..."
	uv run --python $(PYTHON_EXEC) -- playwright install --with-deps chromium 
	@echo "Installation complete. Activate with: source $(VENV_DIR)/bin/activate"
	@echo "Or run commands via make targets (e.g., make extract)."

# Target for the backfill script using uv run
.PHONY: extract
extract: check-uv $(VENV_DIR)/bin/activate # Ensure venv exists and is notionally checked
	@if [ -z "$(START_DATE)" ] || [ -z "$(END_DATE)" ]; then \
		echo "Error: START_DATE and END_DATE must be set."; \
		echo "Usage: make extract START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD [DELAY_SECONDS=N]"; \
		exit 1; \
	fi
	@echo "Running backfill from $(START_DATE) to $(END_DATE) using uv environment..."
	@DELAY_ARG=""
	@if [ -n "$(DELAY_SECONDS)" ] && [ "$(DELAY_SECONDS)" -gt 0 ]; then \
		DELAY_ARG="--delay $(DELAY_SECONDS)"; \
		echo "With a delay of $(DELAY_SECONDS) seconds between downloads."; \
	fi
	uv run --python $(PYTHON_EXEC) -- python -m src.etl.extract.backfill_by_month $(START_DATE) $(END_DATE) $${DELAY_ARG}

# A phony target to represent the venv activation, used as a prerequisite.
# This doesn't actually activate it for the whole make session, but uv run handles context.
$(VENV_DIR)/bin/activate:
	@if [ ! -f "$(VENV_DIR)/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi 


# Target to run all transformation steps (create raw and refined views)
.PHONY: transform
transform: 
	@echo "Creating raw and refined models.."
	uv run --python $(PYTHON_EXEC) -- python -m src.etl.transform.create_raw_contracts_model
	uv run --python $(PYTHON_EXEC) -- python -m src.etl.transform.create_refined_contracts_model
	@echo "All transformation steps completed. Raw and refined views created/updated." 