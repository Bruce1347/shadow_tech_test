import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import scoped_session

from src.api.main import database_connection, init_api
from src.database.common import BaseModel
from typing import Generator


@pytest.fixture(autouse=True)
def app() -> Generator[FastAPI, None, None]:
    app = init_api()

    yield app


def get_testing_db() -> Generator[scoped_session, None, None]:
    from src.api.main import session_factory

    session = scoped_session(session_factory)()

    yield session


@pytest.fixture(scope="function", autouse=True)
def create_db(request):
    from src.api.main import engine

    BaseModel.metadata.drop_all(bind=engine)
    BaseModel.metadata.create_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def session(app: FastAPI) -> Generator[scoped_session, None, None]:
    app.dependency_overrides[database_connection] = get_testing_db

    session = next(get_testing_db())

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(app: FastAPI) -> Generator[TestClient, None, None]:
    client = TestClient(app)

    yield client
