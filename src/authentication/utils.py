from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.api import config
from jose import jwt


def create_access_token(data: dict, expires_delta: int):
    to_encode = data.copy()
    expire_time = datetime.now(ZoneInfo(config.APP_TZ)) + timedelta(
        minutes=expires_delta
    )
    to_encode.update({"exp": expire_time})

    return jwt.encode(
        to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_HASH_ALGORITHM
    )
