# Mystery Music Machine - Development Makefile
# ================================================
# 
# This Makefile provides convenient commands for development, testing, and running
# the Raspberry Pi engine. All Python operations are performed within the project's
# virtual environment as required by the project specification.
#
# Usage:
#   make help         - Show this help message
#   make setup        - Initial setup and dependency installation
#   make test         - Run all tests
#   make run          - Start the RPI engine
#   make clean        - Clean up temporary files
#   make lint         - Run code quality checks
#   make verify       - Verify setup and run basic functionality tests

.PHONY: help setup test run clean lint verify install-deps activate check-venv

# Default target
.DEFAULT_GOAL := help

# Project paths
PROJECT_ROOT := $(shell pwd)
VENV_PATH := $(PROJECT_ROOT)/.venv
VENV_BIN := $(VENV_PATH)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
ENGINE_SRC := $(PROJECT_ROOT)/src
ENGINE_TESTS := $(PROJECT_ROOT)/tests
ENGINE_CONFIG := $(PROJECT_ROOT)/config.yaml
ENGINE_REQUIREMENTS := $(PROJECT_ROOT)/requirements.txt

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Mystery Music Machine - Development Commands$(NC)"
	@echo "=============================================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Virtual Environment Notes:$(NC)"
	@echo "  All Python operations are performed within .venv/"
	@echo "  Run 'make setup' first if this is a fresh clone"
	@echo ""

check-venv: ## Check if virtual environment exists and is activated
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(RED)❌ Virtual environment not found at $(VENV_PATH)$(NC)"; \
		echo "$(YELLOW)Run 'make setup' to create it$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "$(RED)❌ Python not found in virtual environment$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Virtual environment ready$(NC)"

setup: ## Initial setup - create venv and install dependencies
	@echo "$(GREEN)Setting up Mystery Music Machine development environment...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv $(VENV_PATH); \
	else \
		echo "$(GREEN)✓ Virtual environment already exists$(NC)"; \
	fi
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r $(ENGINE_REQUIREMENTS)
	@$(PIP) install pytest pytest-cov  # Development dependencies
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  make verify    - Verify installation"
	@echo "  make test      - Run tests"
	@echo "  make run       - Start the engine"

install-deps: check-venv ## Install/update Python dependencies
	@echo "$(YELLOW)Installing/updating dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r $(ENGINE_REQUIREMENTS)
	@$(PIP) install pytest pytest-cov
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

verify: check-venv ## Verify setup and run basic functionality tests
	@echo "$(GREEN)Running setup verification...$(NC)"
	@chmod +x verify_setup.sh
	@./verify_setup.sh

test: check-venv ## Run all tests
	@echo "$(GREEN)Running test suite...$(NC)"
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS) -v

test-verbose: check-venv ## Run tests with verbose output and coverage
	@echo "$(GREEN)Running test suite with coverage...$(NC)"
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS) -v --cov=$(ENGINE_SRC) --cov-report=term-missing

test-integration: check-venv ## Run only integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS)/test_integration_phase2.py -v

test-unit: check-venv ## Run only unit tests (exclude integration)
	@echo "$(GREEN)Running unit tests...$(NC)"
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS) -v -k "not integration"

run: check-venv ## Start the RPI engine with default config
	@echo "$(GREEN)Starting Mystery Music Engine...$(NC)"
	@echo "$(YELLOW)Config: $(ENGINE_CONFIG)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@echo ""
	@cd $(PROJECT_ROOT) && $(PYTHON) $(ENGINE_SRC)/main.py --config $(ENGINE_CONFIG) --log-level INFO

run-debug: check-venv ## Start the RPI engine with debug logging
	@echo "$(GREEN)Starting Mystery Music Engine (DEBUG mode)...$(NC)"
	@echo "$(YELLOW)Config: $(ENGINE_CONFIG)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@echo ""
	@cd $(PROJECT_ROOT) && $(PYTHON) $(ENGINE_SRC)/main.py --config $(ENGINE_CONFIG) --log-level DEBUG

run-config: check-venv ## Start the RPI engine with custom config (usage: make run-config CONFIG=path/to/config.yaml)
	@if [ -z "$(CONFIG)" ]; then \
		echo "$(RED)❌ Please specify CONFIG variable: make run-config CONFIG=path/to/config.yaml$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(CONFIG)" ]; then \
		echo "$(RED)❌ Config file not found: $(CONFIG)$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Starting Mystery Music Engine...$(NC)"
	@echo "$(YELLOW)Config: $(CONFIG)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@echo ""
	@cd $(PROJECT_ROOT) && $(PYTHON) $(ENGINE_SRC)/main.py --config $(CONFIG) --log-level INFO

lint: check-venv ## Run code quality checks (requires flake8)
	@echo "$(GREEN)Running code quality checks...$(NC)"
	@if ! $(PYTHON) -c "import flake8" 2>/dev/null; then \
		echo "$(YELLOW)Installing flake8...$(NC)"; \
		$(PIP) install flake8; \
	fi
	@$(VENV_BIN)/flake8 $(ENGINE_SRC) --max-line-length=100 --ignore=E501,W503 || echo "$(YELLOW)⚠️  Lint warnings found$(NC)"

format: check-venv ## Format code with black (requires black)
	@echo "$(GREEN)Formatting code...$(NC)"
	@if ! $(PYTHON) -c "import black" 2>/dev/null; then \
		echo "$(YELLOW)Installing black...$(NC)"; \
		$(PIP) install black; \
	fi
	@$(VENV_BIN)/black $(ENGINE_SRC) $(ENGINE_TESTS) --line-length=100

check-imports: check-venv ## Check if all Phase 2 modules can be imported
	@echo "$(GREEN)Checking Phase 2 module imports...$(NC)"
	@cd $(PROJECT_ROOT) && $(PYTHON) -c "import sys; sys.path.insert(0, '$(ENGINE_SRC)'); import state; import sequencer; import action_handler; print('✓ All Phase 2 modules imported successfully')"

clean: ## Clean up temporary files and caches
	@echo "$(GREEN)Cleaning up temporary files...$(NC)"
	@find $(PROJECT_ROOT) -name "*.pyc" -delete
	@find $(PROJECT_ROOT) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -name "*.pyo" -delete
	@find $(PROJECT_ROOT) -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf $(VENV_PATH)
	@echo "$(GREEN)✓ Complete cleanup finished$(NC)"
	@echo "$(YELLOW)Run 'make setup' to recreate the environment$(NC)"

dev-shell: check-venv ## Start an interactive Python shell with engine modules loaded
	@echo "$(GREEN)Starting development shell...$(NC)"
	@echo "$(YELLOW)Engine modules are pre-loaded in sys.path$(NC)"
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTHON) -i -c "import sys; sys.path.insert(0, '$(ENGINE_SRC)'); print('Ready! Try: import state, sequencer, action_handler')"

status: ## Show project status and environment info
	@echo "$(GREEN)Mystery Music Machine - Project Status$(NC)"
	@echo "======================================"
	@echo ""
	@echo "$(YELLOW)Project Root:$(NC) $(PROJECT_ROOT)"
	@echo "$(YELLOW)Virtual Env:$(NC) $(VENV_PATH)"
	@echo ""
	@if [ -d "$(VENV_PATH)" ]; then \
		echo "$(GREEN)✓ Virtual environment exists$(NC)"; \
		if [ -f "$(PYTHON)" ]; then \
			echo "$(GREEN)✓ Python available:$(NC) $$($(PYTHON) --version)"; \
		else \
			echo "$(RED)❌ Python not found in venv$(NC)"; \
		fi \
	else \
		echo "$(RED)❌ Virtual environment missing$(NC)"; \
	fi
	@echo ""
	@if [ -f "$(ENGINE_CONFIG)" ]; then \
		echo "$(GREEN)✓ Engine config found:$(NC) $(ENGINE_CONFIG)"; \
	else \
		echo "$(RED)❌ Engine config missing:$(NC) $(ENGINE_CONFIG)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Engine Source:$(NC) $(ENGINE_SRC)"
	@echo "$(YELLOW)Engine Tests:$(NC) $(ENGINE_TESTS)"
	@echo ""

# Development convenience targets
dev: setup verify ## Quick development setup (setup + verify)
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Quick commands:$(NC)"
	@echo "  make test      - Run tests"
	@echo "  make run       - Start engine"
	@echo "  make help      - Show all commands"

# Git helper targets
tag-version: ## Create a git tag (usage: make tag-version VERSION=v0.0.3)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)❌ Please specify VERSION: make tag-version VERSION=v0.0.3$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Creating git tag: $(VERSION)$(NC)"
	@git tag $(VERSION)
	@echo "$(YELLOW)Push with: git push origin $(VERSION)$(NC)"

# Maintenance targets
update: check-venv ## Update all dependencies to latest versions
	@echo "$(GREEN)Updating dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install --upgrade -r $(ENGINE_REQUIREMENTS)
	@$(PIP) install --upgrade pytest pytest-cov
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

# Documentation helpers
readme: ## Display README.md in terminal
	@cat README.md

spec: ## Display SPEC.md in terminal
	@cat docs/AI/SPEC.md

# Quick test targets for specific components
test-state: check-venv ## Test state management module
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS)/test_state.py -v

test-sequencer: check-venv ## Test sequencer module
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS)/test_sequencer.py -v

test-router: check-venv ## Test router module
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS)/test_router.py -v

test-actions: check-venv ## Test action handler module
	@cd $(PROJECT_ROOT) && PYTHONPATH=$(ENGINE_SRC) $(PYTEST) $(ENGINE_TESTS)/test_action_handler.py -v
