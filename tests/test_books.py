from copy import deepcopy
from http import HTTPStatus
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database.models import Author, Book


class TestCreateBooks:
    @pytest.fixture
    def book_payload(self) -> Generator[dict[str, str | int], None, None]:
        yield {
            "title": "Leviathan Wakes",
        }

    def test_create(
        self,
        test_client: TestClient,
        book_payload: dict[str, str | int],
        session: Session,
    ) -> None:
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        session.add(author)
        session.commit()

        book_payload["author_id"] = author.id

        response = test_client.post(
            "/books/",
            json=book_payload,
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {
            # ``id`` is an autoincremented int and no books are the database.
            # This makes it predictable.
            "id": 1,
            "title": "Leviathan Wakes",
            "author": {
                "id": author.id,
                "first_name": "James S.A.",
                "last_name": "Corey",
            },
            "author_id": author.id,
            "isbn": None,
            "available": True,
        }

    def test_create_with_malformed_payload(
        self,
        test_client: TestClient,
        book_payload: dict[str, Any],
        session: Session,
    ) -> None:
        # Avoid side effects through a deep copy
        payload = deepcopy(book_payload)

        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        session.add(author)
        session.commit()

        payload["author_id"] = author.id
        payload.pop("title")

        response = test_client.post(
            "/books/",
            json=payload,
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        returned_payload = response.json()

        assert "detail" in returned_payload
        # Only one error expected
        assert len(returned_payload["detail"]) == 1

        error_detail = returned_payload["detail"][0]

        assert error_detail["loc"] == ["body", "title"]
        assert error_detail["msg"] == "Field required"


class TestReadBooks:
    def test_get_book(
        self,
        test_client: TestClient,
        session: Session,
    ) -> None:
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        book = Book(
            title="Leviathan Wakes",
            # Populate the author through the relationship instead of using ``author.id``,
            # its id hasn't been generated yet since it's an autoincremented int that is
            # generated by the DB.
            author=author,
        )

        session.add(author)
        session.add(book)

        session.commit()

        response = test_client.get(f"/books/{book.id}")

        assert response.status_code == HTTPStatus.OK

        received_payload = response.json()

        assert received_payload == {
            "id": book.id,
            "author_id": author.id,
            "author": {
                "id": author.id,
                "first_name": "James S.A.",
                "last_name": "Corey",
            },
            "title": "Leviathan Wakes",
            "isbn": None,
            "available": True,
        }

    def test_get_book_wrong_id(
        self,
        test_client: TestClient,
    ) -> None:
        response = test_client.get("/books/1")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_get_books_with_no_books_in_db(
        self,
        test_client: TestClient,
    ) -> None:
        response = test_client.get("/books")

        assert response.status_code == HTTPStatus.OK

        assert len(response.json()) == 0

    def test_get_books(
        self,
        test_client: TestClient,
        session: Session,
    ) -> None:
        james_corey = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        dennis_taylor = Author(
            first_name="Dennis E.",
            last_name="Taylor",
        )
        leviathan_wakes = Book(
            title="Leviathan Wakes",
            author=james_corey,
        )
        calibans_war = Book(
            title="Caliban's War",
            author=james_corey,
        )
        we_are_bob = Book(
            title="We Are Legion (We Are Bob)",
            author=dennis_taylor,
        )

        session.add_all(
            [james_corey, dennis_taylor],
        )
        session.add_all(
            [leviathan_wakes, calibans_war, we_are_bob],
        )

        session.commit()

        response = test_client.get("/books")

        assert response.status_code == HTTPStatus.OK

        assert len(response.json()) == 3


class TestUpdateBooks:
    @pytest.fixture
    def update_payload(self) -> Generator[dict[str, str | int], None, None]:
        yield {
            "id": 1,
            "author_id": 1,
            "title": "Leviathan Wakes",
        }

    def test_update_book_wrong_id(
        self,
        test_client: TestClient,
        update_payload: dict[str, str | int],
    ) -> None:
        response = test_client.put(
            "/books/1",
            json=update_payload,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_update_book(
        self,
        test_client: TestClient,
        session: Session,
        update_payload: dict[str, str | int],
    ) -> None:
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        book = Book(
            title="Leviathan Wakes",
            author=author,
        )

        session.add(author)
        session.add(book)

        session.commit()

        payload = deepcopy(update_payload)

        payload["title"] = "Caliban's War"

        session.expire_all()

        response = test_client.put(
            f"/books/{book.id}",
            json=payload,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "id": book.id,
            "author_id": author.id,
            "author": {
                "id": author.id,
                "first_name": "James S.A.",
                "last_name": "Corey",
            },
            "title": "Caliban's War",
            "isbn": None,
            "available": True,
        }

    @pytest.mark.parametrize("missing_field", ["author_id", "title"])
    def test_update_book_missing_field(
        self,
        missing_field: str,
        test_client: TestClient,
        session: Session,
        update_payload: dict[str, str | int],
    ) -> None:
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        book = Book(
            title="Leviathan Wakes",
            author=author,
        )

        session.add_all([author, book])
        session.commit()

        payload = deepcopy(update_payload)

        payload.pop(missing_field)

        response = test_client.put(
            f"/books/{book.id}",
            json=payload,
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        returned_payload = response.json()

        assert "detail" in returned_payload
        # Only one error expected
        assert len(returned_payload["detail"]) == 1

        error_detail = returned_payload["detail"][0]

        assert error_detail["loc"] == ["body", missing_field]
        assert error_detail["msg"] == "Field required"


class TestDeleteBook:
    def test_delete_book(
        self,
        test_client: TestClient,
        session: Session,
    ) -> None:
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        book = Book(
            title="Leviathan Wakes",
            author=author,
        )

        session.add_all([author, book])
        session.commit()

        # Keep the book id before expiring the session, this is needed to assert the
        # deletion of the object since accessing an expired object will raise an
        # exception.
        book_id = book.id
        session.expire_all()

        response = test_client.delete(f"/books/{book_id}")

        assert response.status_code == HTTPStatus.NO_CONTENT

        assert not Book.exists(book_id, session)

    def test_delete_book_wrong_id(
        self,
        test_client: TestClient,
    ) -> None:
        response = test_client.delete("/books/42")

        assert response.status_code == HTTPStatus.NOT_FOUND
