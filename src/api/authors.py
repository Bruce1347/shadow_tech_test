from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api import main
from src.database.models import Author
from src.schemas.books import AuthorDumpSchema, AuthorSchema

router = APIRouter(
    prefix="/author",
    tags=["author"],
    responses={
        int(HTTPStatus.NOT_FOUND): {"description": "Not found"},
    },
    dependencies=[
        Depends(main.database_connection),
    ],
)


@router.get("/", status_code=int(HTTPStatus.OK))
def get_authors(
    session: Annotated[Session, Depends(main.database_connection)],
) -> list[AuthorDumpSchema]:
    db_authors = Author.get_authors_list(session)

    return [AuthorDumpSchema.model_validate(db_author) for db_author in db_authors]


@router.post("/", status_code=int(HTTPStatus.CREATED))
def create_author(
    author: AuthorSchema,
    session: Annotated[Session, Depends(main.database_connection)],
) -> AuthorDumpSchema:
    db_author = Author.create_object(author, session)

    session.commit()

    return AuthorDumpSchema.model_validate(db_author)


@router.get("/{author_id}", status_code=int(HTTPStatus.OK))
def get_author(
    author_id: int,
    session: Annotated[Session, Depends(main.database_connection)],
) -> AuthorDumpSchema:
    db_author = Author.get(author_id, session)

    if not db_author:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    return AuthorDumpSchema.model_validate(db_author)


@router.put("/{author_id}", status_code=int(HTTPStatus.OK))
def update_author(
    author_id: int,
    author: AuthorDumpSchema,
    session: Annotated[Session, Depends(main.database_connection)],
) -> AuthorDumpSchema:
    db_author = Author.get(author_id, session)

    if not db_author:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    for attr in author.model_fields.keys():
        setattr(db_author, attr, getattr(author, attr))

    session.add(db_author)
    session.commit()

    return AuthorDumpSchema.model_validate(db_author)


@router.delete("/{author_id}", status_code=int(HTTPStatus.NO_CONTENT))
def delete_author(
    author_id: int,
    session: Annotated[Session, Depends(main.database_connection)],
) -> None:
    author_deleted = Author.delete(author_id, session)

    if not author_deleted:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    session.commit()

    return
