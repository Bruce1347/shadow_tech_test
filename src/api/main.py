from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.api import config


def create_db_connection(db_uri: str, connect_args=None):
    kwargs = {
        "echo": False,
    }

    engine = create_engine(
        db_uri,
        **kwargs,
    )

    return engine


engine = create_db_connection(
    db_uri=config.SQLALCHEMY_DATABASE_URI,
)

session_factory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def database_test_connection():
    session = scoped_session(session_factory)()

    def commit() -> None:
        session.flush()

    session.commit = commit

    try:
        yield session
    finally:
        breakpoint()


def database_connection():
    session = session_factory()

    try:
        yield session
    finally:
        session.close()


def init_api(*, db_config=None):
    app = FastAPI()

    # Circular imports
    from src.api import authors, books, user

    app.include_router(books.router)
    app.include_router(authors.router)
    app.include_router(user.router)

    return app


if not config.TESTING:
    app = init_api()
