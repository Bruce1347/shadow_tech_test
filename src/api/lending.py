from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from src.api import main, config
from src.database.models import User, Lending, Book
from src.schemas.lending import LendingDumpSchema, LendingEditSchema, LendingSchema
from typing import Annotated, Sequence
from src.api.user import get_logged_user
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy import ColumnExpressionArgument, select
from zoneinfo import ZoneInfo

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


@router.get("/me", status_code=int(HTTPStatus.OK))
def get_my_lendings(
    session: Annotated[Session, Depends(main.database_connection)],
    logged_user: Annotated[User, Depends(get_logged_user)],
) -> list[LendingDumpSchema]:
    filters: list[ColumnExpressionArgument[bool]] = [
        User.id == logged_user.id,
    ]

    return [
        LendingDumpSchema.model_validate(lending)
        for lending in Lending.get_all(filters, session)
    ]


@router.put("/me/{lending_id}", status_code=int(HTTPStatus.OK))
def update_lending(
    lending_id: UUID,
    lending_payload: LendingEditSchema,
    session: Annotated[Session, Depends(main.database_connection)],
    logged_user: Annotated[User, Depends(get_logged_user)],
) -> LendingDumpSchema:
    lending: Lending = Lending.get_or_404(
        lending_id,
        logged_user.id,
        session,
    )

    if lending_payload.end_time < lending.start_time:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    # Check if any lendings on the current book (``lending.book``) were registered with
    # a start date that would be prior to the new end date
    conflicting_lendings_query = select(Lending).where(
        Lending.start_time < lending_payload.end_time,
        Lending.book_id == lending.book_id,
        Lending.id != lending.id,
    )

    conflicting_lendings: Sequence[Lending] = (
        session.execute(conflicting_lendings_query).scalars().all()
    )

    if conflicting_lendings:
        raise HTTPException(status_code=HTTPStatus.CONFLICT)

    for field in LendingEditSchema.model_fields.keys():
        new_field_value = getattr(lending_payload, field)
        setattr(lending, field, new_field_value)

    session.add(lending)
    session.commit()

    return LendingDumpSchema.model_validate(lending)
