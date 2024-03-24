from http import HTTPStatus
import pytest
from fastapi.testclient import TestClient
from uuid import UUID
from src.database.models import User
from copy import deepcopy
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import Generator


class TestCreateUser:
    @pytest.fixture
    def book_payload(self) -> Generator[dict[str, str], None, None]:
        yield {
            "first_name": "Josephus",
            "last_name": "Miller",
            "username": "joe",
            "address": "Ceres Station",
            "email": "joe.miller@example.com",
            "password": "beltalowda42",
        }

    def test_create(
        self,
        test_client: TestClient,
        book_payload: dict[str, str],
        session: Session,
    ) -> None:
        response = test_client.post("/user", json=book_payload)

        assert response.status_code == HTTPStatus.CREATED

        received_payload = response.json()

        assert isinstance(received_payload, dict)
        # Password shouldn't be in the payload
        assert "password" not in received_payload

        assert received_payload["username"] == "joe"
        assert received_payload["first_name"] == "Josephus"
        assert received_payload["last_name"] == "Miller"

        query = select(User).where(User.id == UUID(received_payload["id"]))

        obj = session.execute(query).scalar()

        assert obj is not None
        assert obj.password is not None
        # Password MUST NOT be stored without encryption
        assert obj.password != "beltalowda42"

    @pytest.mark.parametrize(
        "missing_field",
        [
            "username",
            "email",
            "password",
        ],
    )
    def test_create_missing_mandatory_field(
        self,
        missing_field: str,
        test_client: TestClient,
        book_payload: dict[str, str],
        session: Session,
    ) -> None:
        payload = deepcopy(book_payload)
        payload.pop(missing_field)

        response = test_client.post("/user", json=payload)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        returned_payload = response.json()

        assert "detail" in returned_payload
        # Only one error expected
        assert len(returned_payload["detail"]) == 1

        error_detail = returned_payload["detail"][0]

        assert error_detail["loc"] == ["body", missing_field]
        assert error_detail["msg"] == "Field required"

        query = select(func.count(User.id))

        users_count = session.execute(query).scalar()
        assert users_count == 0
