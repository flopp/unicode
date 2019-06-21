.PHONY: setup test flake8 spell deploy

setup:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r requirements-dev.txt

test: flake8 spell

flake8:
	@venv/bin/flake8 www

spell:
	@venv/bin/codespell README.md www/*.py www/templates/*.html

deploy:
	ansible-playbook deploy.yml
