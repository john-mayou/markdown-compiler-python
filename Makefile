.PHONY: ensure_in_venv venv test lint

# ----- Checks -----

check_in_venv:
	@test "$$VIRTUAL_ENV" != "" || (echo "Not in virtual env. Run: make venv" && exit 1)

# ----- Virtual Env -----

venv:
	@echo "Creating virtual environment..."
	@python3.13 -m venv .venv
	@echo "Done. Now run: source .venv/bin/activate"
	@echo "To leave the environment run: deactivate"

# ----- Testing -----

test: check_in_venv
	pytest -s -vv *_test.py

# ----- Linting -----

lint: check_in_venv
	mypy *.py