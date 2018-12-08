test: flake8 spell

flake8:
	@flake8 www

spell:
	@codespell README.md www/*.py www/templates/*.html

deploy:
	ansible-playbook deploy.yml
