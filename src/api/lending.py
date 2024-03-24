from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from src.api import main, config
from src.database.common import LendingException
from src.database.models import User, Lending, Book
from src.schemas.lending import LendingDumpSchema, LendingSchema
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
    lending_payload: LendingSchema,
    book_id: int,
    session: Annotated[Session, Depends(main.database_connection)],
    logged_user: Annotated[User, Depends(get_logged_user)],
) -> LendingDumpSchema:
    book: Book | None = Book.get(book_id, session)

    if not book:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    
    tz = ZoneInfo(config.APP_TZ)

    # Add TZ to provided datetimes
    start_time = lending_payload.start_time
    end_time = lending_payload.end_time
    start_time.replace(tzinfo=tz)
    end_time.replace(tzinfo=tz)

    lending: Lending = Lending.lend_book(
        book,
        user_id=logged_user.id,
        start_time=start_time,
        end_time=end_time,
        session=session,
    )

    session.commit()

    return LendingDumpSchema.model_validate(lending)
