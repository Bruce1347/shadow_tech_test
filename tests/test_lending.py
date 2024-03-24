from src.database.models import Author, Book, User, Lending
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.testclient import TestClient
from src.authentication.utils import create_access_token
from src.api import config
from http import HTTPStatus


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
        payload = {
            "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=40)).isoformat(),
        }

        response = test_client.post(f"/lending/{book.id}", json=payload, headers=headers)

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

        # Lend the current book
        current_lending: Lending = Lending.lend_book(
            book=book,
            user_id=user.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=30),
            session=session,
        )

        assert current_lending
        session.add(current_lending)
        session.commit()

        monkeypatch.setattr(config, "JWT_SECRET_KEY", "my_sup3r_s3cret_k3y")

        token = create_access_token(
            data=dict(sub=user.username),
            expires_delta=10,
        )

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=40)).isoformat(),
        }

        response = test_client.post(f"/lending/{book.id}", json=payload, headers=headers)

        # Current book already has a lending entry that conflicts with the previous start and end times
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json() == {
            "detail": {
                "errors": "Lending failed for Leviathan Wakes: not enough stock"
            },
        }
