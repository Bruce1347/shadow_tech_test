from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from jose import jwt

from src.api import config


def create_access_token(data: dict[str, Any], expires_delta: int) -> str:
    to_encode = data.copy()
    expire_time = datetime.now(ZoneInfo(config.APP_TZ)) + timedelta(
        minutes=expires_delta
    )
    to_encode.update({"exp": expire_time})

    return jwt.encode(
        to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_HASH_ALGORITHM
    )
