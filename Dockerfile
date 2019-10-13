FROM python:3-slim

WORKDIR /app

COPY ./app /app/app
COPY Pipfile Pipfile.lock /

RUN pip install pipenv
RUN cd / && pipenv install --system --deploy --ignore-pipfile

CMD ["/bin/bash", "-c", "python -m app"]

EXPOSE 8080
