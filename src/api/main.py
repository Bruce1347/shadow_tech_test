from fastapi import FastAPI
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api import config

from typing import Any, Generator


def create_db_connection(db_uri: str, **kwargs: dict[str, Any]) -> Engine:
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


def database_connection() -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def init_api() -> FastAPI:
    app: FastAPI = FastAPI()

    # Circular imports
    from src.api import authors, books, user, lending

    app.include_router(books.router)
    app.include_router(authors.router)
    app.include_router(user.router)
    app.include_router(lending.router)

    return app


if not config.TESTING:
    app = init_api()
