from src.database.models import Author, Book, User, Lending
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.testclient import TestClient
from src.authentication.utils import create_access_token
from src.api import config
from http import HTTPStatus
from pytest import MonkeyPatch
from uuid import UUID


def create_test_token(
    user: User,
    patcher: MonkeyPatch,
) -> str:
    patcher.setattr(config, "JWT_SECRET_KEY", "my_sup3r_s3cret_k3y")

    return create_access_token(
        data=dict(sub=user.username),
        expires_delta=10,
    )


class TestLending:
    def test_lend_book(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch: MonkeyPatch,
    ) -> None:
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
        )

        session.add_all([user, author, book])
        session.commit()

        token = create_test_token(user, monkeypatch)

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "start_time": (datetime.now() + timedelta(days=2)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=40)).isoformat(),
        }

        response = test_client.post(
            f"/lending/{book.id}", json=payload, headers=headers
        )

        assert response.status_code == HTTPStatus.OK

        query = select(Lending).where(
            Lending.user_id == user.id,
            Lending.book_id == book.id,
        )

        lending_db_object = session.execute(query).one_or_none()

        assert lending_db_object is not None

    def test_lend_returned_book(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch: MonkeyPatch,
    ) -> None:
        user: User = User(
            username="bruce",
            email="bruce@bruce.tld",
            password="h4xx0r",
        )

        other_user: User = User(
            username="ZeroCool",
            email="zero@cool.tld",
            password="h4xxtehpl4n3t",
        )

        author: Author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        book: Book = Book(
            title="Leviathan Wakes",
            author=author,
        )
        session.add_all([user, other_user, author, book])
        session.commit()

        # Lend the current book
        current_lending: Lending = Lending.lend_book(
            book=book,
            user_id=user.id,
            start_time=datetime(2023, 1, 1),
            end_time=datetime(2023, 2, 1),
            session=session,
        )

        assert current_lending

        # ``user`` returns the book before Feb 1st
        current_lending.return_time = datetime(2023, 1, 25)
        current_lending.is_active = False

        session.add(current_lending)
        session.commit()

        token = create_test_token(other_user, monkeypatch)

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "start_time": datetime(2023, 1, 28).isoformat(),
            "end_time": datetime(2023, 2, 15).isoformat(),
        }

        response = test_client.post(
            f"/lending/{book.id}", json=payload, headers=headers
        )

        # ``other_user`` should be able to borrow the book on Jan 28th
        assert response.status_code == HTTPStatus.OK

    def test_lend_book_without_stock(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch: MonkeyPatch,
    ) -> None:
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

        response = test_client.post(
            f"/lending/{book.id}", json=payload, headers=headers
        )

        # Current book already has a lending entry that conflicts with the previous start and end times
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json() == {
            "detail": {
                "errors": "Lending failed for Leviathan Wakes: not enough stock"
            },
        }


class TestLendingEdition:
    def test_edit_lending(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch: MonkeyPatch,
    ) -> None:
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

        current_lending_id: UUID = current_lending.id

        token = create_test_token(user, monkeypatch)

        session.expire_all()

        headers = {"Authorization": f"Bearer {token}"}
        new_end_time = datetime.now() + timedelta(days=15)
        payload = {
            "end_time": new_end_time.isoformat(),
        }

        response = test_client.put(
            f"/lending/me/{current_lending_id}",
            json=payload,
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK

        edited_lending = session.execute(
            select(Lending).where(
                Lending.id == current_lending_id,
            )
        ).scalar()

        assert edited_lending
        assert edited_lending.end_time == new_end_time

    def test_edit_lending_end_time_before_start(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch: MonkeyPatch,
    ) -> None:
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

        current_lending_id: UUID = current_lending.id

        token = create_test_token(user, monkeypatch)

        session.expire_all()

        headers = {"Authorization": f"Bearer {token}"}
        new_end_time = datetime.now() - timedelta(days=15)
        payload = {
            "end_time": new_end_time.isoformat(),
        }

        response = test_client.put(
            f"/lending/me/{current_lending_id}",
            json=payload,
            headers=headers,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_edit_lending_intersects_with_another(
        self,
        test_client: TestClient,
        session: Session,
        monkeypatch: MonkeyPatch,
    ) -> None:
        first_user: User = User(
            username="bruce",
            email="bruce@bruce.tld",
            password="h4xx0r",
        )

        second_user: User = User(
            username="brucer",
            email="brucer@email.tld",
            password="h4xx",
        )

        author: Author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        book: Book = Book(
            title="Leviathan Wakes",
            author=author,
        )

        session.add_all([first_user, second_user, author, book])
        session.commit()

        # Lend the current book
        first_lending: Lending = Lending.lend_book(
            book=book,
            user_id=first_user.id,
            start_time=datetime(2023, 1, 1),
            end_time=datetime(2023, 1, 15),
            session=session,
        )
        assert first_lending

        session.add(first_lending)
        session.commit()

        # Second user lends the book after user #1
        second_lending: Lending = Lending.lend_book(
            book=book,
            user_id=second_user.id,
            start_time=datetime(2023, 1, 16),
            end_time=datetime(2023, 2, 1),
            session=session,
        )
        assert second_lending

        session.add(first_lending)
        session.commit()

        current_lending_id: UUID = first_lending.id

        token = create_test_token(first_user, monkeypatch)

        session.expire_all()

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "end_time": datetime(2023, 1, 20).isoformat(),
        }

        # First user tries to extend their lending over second user's lending
        response = test_client.put(
            f"/lending/me/{current_lending_id}",
            json=payload,
            headers=headers,
        )

        assert response.status_code == HTTPStatus.CONFLICT
