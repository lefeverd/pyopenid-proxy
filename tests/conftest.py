from flask import Flask
import pytest
from app.app import create_app


@pytest.fixture
def app():
    app: Flask = create_app()
    yield app


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client
