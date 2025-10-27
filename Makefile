UV ?= uv
UVX ?= uvx
FLAVOR ?= cpu
IMAGE_NAME ?= mlops-serving:local

.PHONY: help install sync lint format test dvc pipeline prefect deploy clean

help:
	@echo "Available targets:"
	@echo "  install     Sync locked dependencies (alias: sync)"
	@echo "  lint        Run Ruff + Black checks"
	@echo "  format      Format code with Black and Ruff"
	@echo "  test        Run pytest suite"
	@echo "  dvc         Reproduce the DVC pipeline"
	@echo "  pipeline    Full pipeline + Prefect registration flow"
	@echo "  prefect     Run Prefect flow without image build"
	@echo "  deploy      Prefect flow + Docker image build (use FLAVOR / IMAGE_NAME)"
	@echo "  clean       Remove __pycache__ and build artifacts"

install sync:
	$(UV) sync --frozen

lint:
	$(UV) run ruff check .
	$(UV) run black --check .

format:
	$(UV) run black .
	$(UVX) ruff format .

test:
	$(UV) run pytest -q

dvc:
	$(UV) run dvc repro

pipeline:
	$(UV) run dvc repro --force
	$(UV) run python flows/train_register_deploy.py

prefect:
	$(UV) run python flows/train_register_deploy.py

deploy:
	$(UV) run python flows/train_register_deploy.py -- --build-image true --flavor $(FLAVOR) --image-name $(IMAGE_NAME)

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf .ruff_cache .pytest_cache
