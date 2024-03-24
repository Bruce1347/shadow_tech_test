from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.api import config, main
from src.authentication.utils import create_access_token
from src.database.models import User
from src.schemas.user import UserCreationSchema, UserDumpSchema, UserToken

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


def get_logged_user(
    token: Annotated[
        str, Depends(OAuth2PasswordBearer(tokenUrl="user/token", auto_error=False))
    ],
    session: Annotated[Session, Depends(main.database_connection)],
) -> User:
    unauthorized_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise unauthorized_exception

    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY)
    except JWTError:
        raise unauthorized_exception

    username = payload.get("sub")

    if not username:
        raise unauthorized_exception

    user: User | None = User.get(username, session)

    if not user:
        raise unauthorized_exception

    return user


@router.post(
    "/",
    status_code=int(HTTPStatus.CREATED),
)
def create_user(
    user_payload: UserCreationSchema,
    session: Annotated[Session, Depends(main.database_connection)],
) -> UserDumpSchema:
    user: User = User.create(user_payload, session)

    session.add(user)
    session.commit()

    return UserDumpSchema.model_validate(user)


@router.post(
    "/token",
    status_code=int(HTTPStatus.ACCEPTED),
)
def create_jwt_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(main.database_connection)],
) -> UserToken:
    user = User.authenticate(form_data.username, form_data.password, session)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data=dict(sub=user.username),
        expires_delta=config.JWT_TOKEN_EXPIRE_TIME,
    )

    return UserToken(access_token=token, token_type="bearer")
