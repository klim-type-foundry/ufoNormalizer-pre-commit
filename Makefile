#
# Variables
#
PYTHON_VERSION=$(shell head -1 .python-version)
VENV_DIR=$(CURDIR)/.venv
# Run a command in the repo's venv, regardless of whether it's activated
VENV_EXEC=env VIRTUAL_ENV="$(VENV_DIR)" PATH="$(VENV_DIR)/bin:$$PATH"

.PHONY: init update test

#
# Commands
#

# Set up the Python environment in .venv and the pre-commit hooks. Needs uv
# (https://docs.astral.sh/uv/)
init:
	@command -v uv >/dev/null || { echo "ERROR: 'uv' not found. See https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
	uv python install --no-bin $(PYTHON_VERSION)
	uv venv --allow-existing --python $(PYTHON_VERSION) --prompt .venv "$(VENV_DIR)"
	@# The exact versions from uv.lock, including this package (editable) and the
	@# development tools
	uv sync --locked
	$(VENV_EXEC) pre-commit install

# Update a single Python package in uv.lock, and install it, e.g.
# `make update dependency=ufonormalizer`
update:
	uv lock --upgrade-package $(dependency)
	uv sync --locked

# Run unit tests
test:
	$(VENV_EXEC) pytest
