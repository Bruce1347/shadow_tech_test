from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from src.schemas.books import BookSchema, BookDumpSchema
from src.database.models import Book
from typing import Annotated
from sqlalchemy.orm import Session

from src.api import main


router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={
        int(HTTPStatus.NOT_FOUND): {"description": "Not found"},
    },
    dependencies=[
        Depends(main.database_connection),
    ],
)


@router.post("/", status_code=int(HTTPStatus.CREATED))
def create_book(
    book: BookSchema,
    session: Annotated[Session, Depends(main.database_connection)],
) -> BookDumpSchema:
    db_object: Book = Book.create(book, session)

    session.commit()

    return BookDumpSchema.model_validate(db_object, from_attributes=True)


@router.get("/", status_code=int(HTTPStatus.OK))
def get_books(
    session: Annotated[Session, Depends(main.database_connection)],
) -> list[BookDumpSchema]:
    books: list[Book] = Book.get_all(session)

    return [BookDumpSchema.model_validate(book) for book in books]


@router.get("/{book_id}", status_code=int(HTTPStatus.OK))
def get_book(
    book_id: int,
    session: Annotated[Session, Depends(main.database_connection)],
) -> BookDumpSchema:
    book: Book | None = Book.get(book_id, session)

    if not book:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    return BookDumpSchema.model_validate(book)


@router.put("/{book_id}", status_code=int(HTTPStatus.OK))
def update_book(
    book_id: int,
    payload: BookSchema,
    session: Annotated[Session, Depends(main.database_connection)],
) -> BookDumpSchema:
    book: Book | None = Book.get(book_id, session)

    if not book:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    for attr in payload.model_fields.keys():
        setattr(book, attr, getattr(payload, attr))

    session.add(book)
    session.commit()

    return BookDumpSchema.model_validate(book)


@router.delete("/{book_id}", status_code=int(HTTPStatus.NO_CONTENT))
def delete_book(
    book_id: int,
    session: Annotated[Session, Depends(main.database_connection)],
) -> None:
    book_deleted: bool = Book.delete(book_id, session)

    if not book_deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    return
