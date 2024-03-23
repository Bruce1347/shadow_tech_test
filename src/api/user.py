from http import HTTPStatus
from fastapi import APIRouter, Depends
from src.api import main
from typing import Annotated
from sqlalchemy.orm import Session
from src.schemas.user import UserCreationSchema, UserDumpSchema
from src.database.models import User

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={
        int(HTTPStatus.NOT_FOUND): {"description": "Not found"},
    },
    dependencies=[
        Depends(main.database_connection),
    ],
)

@router.post(
    "/",
    status_code=int(HTTPStatus.CREATED),
)
def create_user(
    user: UserCreationSchema,
    session: Annotated[Session, Depends(main.database_connection)]
):
    user: User = User.create(user, session)

    session.add(user)
    session.commit()

    return UserDumpSchema.model_validate(user)