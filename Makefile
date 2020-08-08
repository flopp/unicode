.PHONY: setup
setup:
	python3 -m venv .env
	.env/bin/pip install --upgrade pip
	.env/bin/pip install -r requirements.txt

.PHONY: setup-dev
setup-dev: setup
	.env/bin/pip install -r requirements-dev.txt

.PHONY: install
install: setup
	.env/bin/pip install .


.PHONY: lint
lint: mypy
	.env/bin/pylint \
	    unicode
	.env/bin/black \
	    --line-length 120 \
	    --check \
	    --diff \
	    unicode

.PHONY: mypy
mypy:
	.env/bin/mypy \
	    unicode

.PHONY: format
format:
	.env/bin/black \
	    --line-length 120 \
	    unicode

.PHONY: run
run: setup
	PYTHONPATH=. .env/bin/python unicode/cli.py \
		--config config-example.py \
		--verbose

.PHONY: run-reset
run-reset: setup
	PYTHONPATH=. .env/bin/python unicode/cli.py \
		--config config-example.py \
		--reset \
		--verbose
