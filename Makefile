PYTHON ?= python3
VERSION_FILE ?= VERSION
INSTALL_PREFIX ?=
KIND_CLUSTER_NAME ?= hape
KIND_CONFIG_PATH ?= infrastructure/kubernetes/kind/cluster-config.yaml

.PHONY: help clean bump-version build install kind-up kind-down

help: ## Show available commands.
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | \
	awk -F ':.*?## ' '{printf "%-20s %s\n", $$1, $$2}' | \
	sort

clean: ## Remove build artifacts.
	@echo "$$ rm -rf build dist *.egg-info"
	@rm -rf build dist *.egg-info

bump-version: ## Bump the patch version in VERSION.
	@version=$$(cat $(VERSION_FILE)); \
	major=$$(echo $$version | cut -d. -f1); \
	minor=$$(echo $$version | cut -d. -f2); \
	patch=$$(echo $$version | cut -d. -f3); \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	echo $$new_version > $(VERSION_FILE); \
	echo "Version updated to $$new_version"

build: bump-version ## Build sdist and wheel into dist/.
	@echo "$$ rm -rf dist"
	@rm -rf dist
	@echo "$$ $(PYTHON) -m build"
	@$(PYTHON) -m build

install: ## Install to $(INSTALL_PREFIX)/bin via pip.
	@wheel=$$(ls -t dist/*.whl 2>/dev/null | head -n 1); \
	if [ -z "$$wheel" ]; then \
		echo "No wheels found in dist/"; \
		exit 1; \
	fi; \
	if [ -n "$(INSTALL_PREFIX)" ]; then \
		echo "$$ $(PYTHON) -m pip install --upgrade --force-reinstall --prefix $(INSTALL_PREFIX) $$wheel"; \
		$(PYTHON) -m pip install --upgrade --force-reinstall --prefix $(INSTALL_PREFIX) $$wheel; \
	else \
		echo "$$ $(PYTHON) -m pip install --upgrade --force-reinstall $$wheel"; \
		$(PYTHON) -m pip install --upgrade --force-reinstall $$wheel; \
	fi

kind-up: ## Create local kind cluster named $(KIND_CLUSTER_NAME).
	@if kind get clusters | grep -xq "$(KIND_CLUSTER_NAME)"; then \
		echo "kind cluster $(KIND_CLUSTER_NAME) is already running"; \
	else \
		kind create cluster --name $(KIND_CLUSTER_NAME) --config $(KIND_CONFIG_PATH); \
	fi

kind-down: ## Delete local kind cluster named $(KIND_CLUSTER_NAME).
	@if kind get clusters | grep -xq "$(KIND_CLUSTER_NAME)"; then \
		kind delete cluster --name $(KIND_CLUSTER_NAME); \
	else \
		echo "kind cluster $(KIND_CLUSTER_NAME) is not running"; \
	fi