.PHONY: init run

init:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

run:
	set -a && source .env.local && set +a && ./venv/bin/python -m app

run-mock:
	set -a && source .env.local.mock && set +a && ./venv/bin/python -m app

run-redis:
	set -a && source .env.local.redis && set +a && ./venv/bin/python -m app

test:
	set -a && source .env.test && set +a && ./venv/bin/pytest tests/
	set -a && source .env.test && set +a && ./venv/bin/pytest tests_integration/
