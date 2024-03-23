from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from src.api import main, config
from src.database.common import LendingException
from src.database.models import User, Lending, Book
from src.schemas.lending import LendingSchema
from typing import Annotated
from src.api.user import get_logged_user
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/lending",
    tags=["lending"],
    responses={
        int(HTTPStatus.NOT_FOUND): {"description": "Not found"},
    },
    dependencies=[
        Depends(main.database_connection),
    ],
)


@router.post("/{book_id}", status_code=int(HTTPStatus.OK))
def reserve_book(
    book_id: int,
    session: Annotated[Session, Depends(main.database_connection)],
    logged_user: Annotated[User, Depends(get_logged_user)],
) -> LendingSchema:
    book: Book = Book.get(book_id, session)

    if not book:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    try:
        lending = Lending(
            user=logged_user,
            book=book,
            start_time=datetime.now(ZoneInfo(config.APP_TZ)),
            end_time=datetime.now(ZoneInfo(config.APP_TZ)) + timedelta(days=30),
        )
        session.add(lending)
        session.commit()
    except LendingException:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"errors": f"Lending failed for {book.title}: not enough stock"},
        )
    else:
        return LendingSchema.model_validate(lending)
