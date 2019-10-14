FROM python:3-slim

WORKDIR /app

COPY ./app /app/app
COPY ./tests /app/tests
COPY ./tests_integration /app/tests_integration
COPY requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["/bin/bash", "-c", "python -m app"]

EXPOSE 8080
