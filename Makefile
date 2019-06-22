.PHONY: setup test flake8 spell pylint check-format deploy

setup:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r requirements-dev.txt

test: flake8 spell pylint 

flake8:
	@venv/bin/flake8 www

pylint:
	@venv/bin/pylint www/*.py

check-format:
	@venv/bin/black --check www/*.py

mypy:
	@venv/bin/mypy --ignore-missing-imports -m www

spell:
	@venv/bin/codespell README.md www/*.py www/templates/*.html

format:
	@venv/bin/black www/*.py

deploy:
	ansible-playbook deploy.yml
