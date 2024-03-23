import pytest

from src.database.models import Author, Book, User, Lending
from src.database.common import LendingException
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.testclient import TestClient
from src.authentication.utils import create_access_token
from src.api import config
from http import HTTPStatus


class TestLendingListener:
    def test_over_lending(self, session):
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        book = Book(
            title="Leviathan Wakes",
            author=author,
            total_stock=2,
        )
        user = User(
            username="bob",
            email="bob@example.org",
            password="h4xx3r",
        )

        session.add_all([author, book, user])
        session.commit()

        for i in range(2):
            lending = Lending(
                user=user,
                book=book,
                start_time=date(2024, 1, 1) + timedelta(days=15 * i),
                end_time=date(2024, 1, 31) + timedelta(days=15 * i),
            )
            session.add(lending)
            session.flush()

        session.commit()

        # Only two books are available, lending a third one is not possible
        with pytest.raises(LendingException):
            lending = Lending(
                user=user,
                book=book,
                start_time=date(2024, 1, 1),
                end_time=date(2024, 1, 31),
            )
            session.add(lending)
            session.commit()


class TestLending:
    def test_lend_book(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch,
    ):
        user: User = User(
            username="bruce",
            email="bruce@bruce.tld",
            password="h4xx0r",
        )

        author: Author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        book: Book = Book(
            title="Leviathan Wakes",
            author=author,
            total_stock=1,
        )

        session.add_all([user, author, book])
        session.commit()

        monkeypatch.setattr(config, "JWT_SECRET_KEY", "my_sup3r_s3cret_k3y")

        token = create_access_token(
            data=dict(sub=user.username),
            expires_delta=10,
        )

        headers = {"Authorization": f"Bearer {token}"}

        response = test_client.post(f"/lending/{book.id}", headers=headers)

        assert response.status_code == HTTPStatus.OK

        query = select(Lending).where(
            Lending.user_id == user.id,
            Lending.book_id == book.id,
        )

        lending_db_object = session.execute(query).one_or_none()

        assert lending_db_object is not None

    def test_lend_book_without_stock(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch,
    ):
        user: User = User(
            username="bruce",
            email="bruce@bruce.tld",
            password="h4xx0r",
        )

        author: Author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        book: Book = Book(
            title="Leviathan Wakes",
            author=author,
            total_stock=0,
        )

        session.add_all([user, author, book])
        session.commit()

        monkeypatch.setattr(config, "JWT_SECRET_KEY", "my_sup3r_s3cret_k3y")

        token = create_access_token(
            data=dict(sub=user.username),
            expires_delta=10,
        )

        headers = {"Authorization": f"Bearer {token}"}

        response = test_client.post(f"/lending/{book.id}", headers=headers)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json() == {
            "detail": {
                "errors": "Lending failed for Leviathan Wakes: not enough stock"
            },
        }
