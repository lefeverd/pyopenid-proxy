FROM python:3.7.0-slim

WORKDIR /app

COPY ./app /app/app
COPY ./tests /app/tests
COPY ./tests_integration /app/tests_integration
COPY requirements.txt /app/

RUN apt-get update \
    && apt-get install -y gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt \
    && apt-get purge -y --auto-remove gcc

CMD ["/bin/bash", "-c", "python -m app"]

EXPOSE 8080
