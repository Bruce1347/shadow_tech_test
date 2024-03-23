import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import scoped_session

from src.api.main import database_connection, init_api
from src.database.common import BaseModel


@pytest.fixture(autouse=True)
def app():
    app = init_api()

    yield app


def get_db():
    from src.api.main import session_factory

    session = scoped_session(session_factory)()

    yield session


@pytest.fixture(scope="function", autouse=True)
def create_db(request):
    from src.api.main import engine

    BaseModel.metadata.drop_all(bind=engine)
    BaseModel.metadata.create_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def session(app, create_db):
    app.dependency_overrides[database_connection] = get_db

    session = next(get_db())

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(app):
    client = TestClient(app)

    yield client
