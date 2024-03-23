from copy import deepcopy
from http import HTTPStatus

import pytest

from src.database.models import Author
from sqlalchemy import select


class TestCreateAuthor:
    @pytest.fixture
    def author_payload(self):
        yield {
            "id": 1,
            "first_name": "James S.A.",
            "last_name": "Corey",
        }

    def test_create(
        self,
        test_client,
        author_payload: dict[str, str],
        session,
    ):
        response = test_client.post(
            "/author/",
            json=author_payload,
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {
            # Id is an autoincremented int, making it a predicatable value
            "id": 1,
            "first_name": "James S.A.",
            "last_name": "Corey",
        }

    def test_create_no_payload(
        self,
        test_client,
    ):
        response = test_client.post("/author/", json={})

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        received_payload = response.json()

        assert len(received_payload["detail"]) == 2

        missing_fields = sorted(
            [error_dict["loc"] for error_dict in received_payload["detail"]]
        )

        assert (
            sorted(
                [
                    ["body", "first_name"],
                    ["body", "last_name"],
                ]
            )
            == missing_fields
        )

    @pytest.mark.parametrize(
        "field_name",
        ["first_name", "last_name"],
    )
    def test_create_missing_field(
        self,
        field_name,
        test_client,
        author_payload,
        session,
    ):
        payload = deepcopy(author_payload)

        payload.pop(field_name)

        response = test_client.post(
            "/author/",
            json=payload,
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        returned_payload = response.json()

        assert "detail" in returned_payload
        # Only one error expected
        assert len(returned_payload["detail"]) == 1

        error_detail = returned_payload["detail"][0]

        assert error_detail["loc"] == ["body", field_name]
        assert error_detail["msg"] == "Field required"


class TestReadAuthor:
    def test_get_author(
        self,
        test_client,
        session,
    ):
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        session.add(author)
        session.commit()

        response = test_client.get(
            f"/author/{author.id}",
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "id": author.id,
            "first_name": "James S.A.",
            "last_name": "Corey",
        }

    def test_get_authors(
        self,
        test_client,
        session,
    ):
        james_corey = Author(
            first_name="James S.A.",
            last_name="Corey",
        )
        becky_chambers = Author(
            first_name="Becky",
            last_name="Chambers",
        )

        session.add(james_corey)
        session.add(becky_chambers)
        session.commit()

        response = test_client.get("/author/")

        assert response.status_code == HTTPStatus.OK

        received_payload = response.json()

        assert len(received_payload) == 2

        assert {
            "id": james_corey.id,
            "first_name": "James S.A.",
            "last_name": "Corey",
        } in received_payload

        assert {
            "id": becky_chambers,
            "first_name": "Becky",
            "last_name": "Chambers",
        }

    def test_get_author_not_exists(
        self,
        test_client,
    ):
        # Database is empty, any id should return a 404
        response = test_client.get(
            "/author/1",
        )

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestUpdateAuthor:
    @pytest.fixture
    def author_payload(self):
        yield {
            "id": 1,
            "first_name": "James S.A.",
            "last_name": "Corey",
        }

    def test_update_author(
        self,
        test_client,
        session,
        author_payload,
    ):
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        session.add(author)
        session.commit()

        author_payload["id"] = author.id
        author_payload["first_name"] = "James"

        response = test_client.put(
            "/author/1",
            json=author_payload,
        )

        assert response.status_code == HTTPStatus.OK

        assert response.json() == {
            "id": author.id,
            "first_name": "James",
            "last_name": "Corey",
        }

        session.expire_all()

        # Check the changed data has been properly persisted
        query = select(Author).filter(Author.id == author.id)
        db_object = session.execute(query).scalar()

        assert db_object.first_name == "James"

    @pytest.mark.parametrize(
        "field_name",
        ["first_name", "last_name"],
    )
    def test_update_author_missing_field(
        self,
        field_name,
        test_client,
        session,
        author_payload,
    ):
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        session.add(author)
        session.commit()

        author_payload["id"] = author.id
        author_payload.pop(field_name)

        response = test_client.put(
            f"/author/{author.id}",
            json=author_payload,
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        returned_payload = response.json()

        assert "detail" in returned_payload
        # Only one error expected
        assert len(returned_payload["detail"]) == 1

        error_detail = returned_payload["detail"][0]

        assert error_detail["loc"] == ["body", field_name]
        assert error_detail["msg"] == "Field required"

    def test_update_author_wrong_id(self, test_client, author_payload, session):
        response = test_client.put(
            "/author/1",
            json=author_payload,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestDeleteAuthor:
    def test_delete_author_wrong_id(
        self,
        test_client,
    ):
        response = test_client.delete(
            "/author/1",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_delete_author(
        self,
        test_client,
        session,
    ):
        author = Author(
            first_name="James S.A.",
            last_name="Corey",
        )

        session.add(author)
        session.commit()

        response = test_client.delete(
            "/author/1",
        )

        assert response.status_code == HTTPStatus.NO_CONTENT

        assert session.query(Author).count() == 0
