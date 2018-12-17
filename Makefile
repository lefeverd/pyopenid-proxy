.PHONY: init run

init:
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

run:
	PIPENV_DOTENV_LOCATION=.env.local pipenv run python -m app

run-mock:
	PIPENV_DOTENV_LOCATION=.env.local.mock pipenv run python -m app

run-redis:
	PIPENV_DOTENV_LOCATION=.env.local.redis pipenv run python -m app

test:
	PIPENV_DOTENV_LOCATION=.env.tests pipenv run pytest tests/ && \
	PIPENV_DOTENV_LOCATION=.env.tests pipenv run pytest tests_integration/
