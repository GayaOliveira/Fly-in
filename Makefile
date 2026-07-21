NAME = main.py
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
PYTHON = .venv/bin/python

venv_create:
	@test -f pyproject.toml || uv init .
	@test -d .venv || uv venv

install: venv_create
	uv sync

run:
	$(PYTHON) $(NAME)

debug:
	$(PYTHON) -m pdb $(NAME)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

lint:
	-$(PYTHON) -m flake8 --exclude .venv
	-$(PYTHON) -m mypy . $(MYPY_FLAGS)

lint-strict:
	-$(PYTHON) -m flake8 . --exclude .venv
	-$(PYTHON) -m mypy . --strict

.PHONY: install run clean lint lint-strict