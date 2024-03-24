from sqlalchemy import (
    ForeignKey,
    String,
    delete,
    select,
    and_,
    or_,
    ColumnExpressionArgument,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from datetime import datetime
from fastapi import HTTPException
from http import HTTPStatus
from typing import Self, Sequence


from src.database.common import BaseModel
from src.schemas.books import AuthorSchema, BookSchema
from src.schemas.user import UserSchema

import uuid
from passlib.context import CryptContext


class Author(BaseModel):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True)

    first_name: Mapped[str] = mapped_column(String())
    last_name: Mapped[str] = mapped_column(String())

    books: Mapped[list["Book"]] = relationship(back_populates="author")

    @classmethod
    def exists(cls, author_id: int, session: Session) -> bool:
        res: bool = session.query(
            select(cls).where(cls.id == author_id).exists()
        ).scalar()

        return res

    @classmethod
    def get(cls, author_id: int, session: Session) -> "Self | None":
        return session.query(cls).filter(cls.id == author_id).first()

    @classmethod
    def delete(cls, author_id: int, session: Session) -> bool:
        author_exists = cls.exists(author_id, session)
        if not author_exists:
            return False

        query = delete(cls).where(cls.id == author_id)

        session.execute(query)

        return True

    @classmethod
    def get_authors_list(cls, session: Session) -> list[Self]:
        return list(session.execute(select(cls)).scalars().fetchall())

    @classmethod
    def create(cls, validated_data: AuthorSchema, session: Session) -> Self:
        instance = cls(**validated_data.model_dump())

        session.add(instance)

        return instance


class Book(BaseModel):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String())
    isbn: Mapped[str | None] = mapped_column(String(13))

    author_id = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")

    current_lends: Mapped[list["Lending"]] = relationship(back_populates="book")

    @classmethod
    def get(cls, book_id: int, session: Session) -> "Book | None":
        return session.execute(select(cls).filter(cls.id == book_id)).scalar()

    @classmethod
    def get_all(cls, session: Session) -> "list[Book]":
        return list(session.execute(select(cls)).scalars())

    @classmethod
    def create(cls, validated_data: BookSchema, session: Session) -> Self:
        instance = cls(**validated_data.model_dump())

        session.add(instance)

        return instance

    @classmethod
    def exists(cls, book_id: int, session: Session) -> bool:
        res: bool = session.query(
            select(cls).where(cls.id == book_id).exists()
        ).scalar()

        return res

    @classmethod
    def delete(cls, book_id: int, session: Session) -> bool:
        book_exists = cls.exists(book_id, session)
        if not book_exists:
            return False

        query = delete(cls).where(cls.id == book_id)

        session.execute(query)

        session.commit()

        return True


class User(BaseModel):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)

    first_name: Mapped[str | None] = mapped_column(String())
    last_name: Mapped[str | None] = mapped_column(String())
    username: Mapped[str] = mapped_column(String())
    address: Mapped[str | None] = mapped_column(String())
    email: Mapped[str] = mapped_column(String())
    hashed_password: Mapped[str] = mapped_column(String())

    current_lends: Mapped[list["Lending"]] = relationship(back_populates="user")

    @property
    def password(self) -> str:
        return self.hashed_password

    @password.setter
    def password(self, new_password: str) -> None:
        context = CryptContext(schemes=["bcrypt"])
        self.hashed_password = context.hash(new_password)

    @classmethod
    def create(cls, validated_data: UserSchema, session: Session) -> Self:
        instance = cls(**validated_data.model_dump())
        session.add(instance)
        return instance

    @classmethod
    def get(cls, username: str, session: Session) -> "Self | None":
        return session.execute(select(cls).where(cls.username == username)).scalar()

    @classmethod
    def authenticate(
        cls, username: str, password: str, session: Session
    ) -> "User | None":
        user = cls.get(username, session)

        if not user:
            return None

        context = CryptContext(schemes=["bcrypt"])

        if not context.verify(password, user.hashed_password):
            return None

        return user


class Lending(BaseModel):
    """Represents the lending of a book by a given user."""

    __tablename__ = "lending"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("book.id"), nullable=False)

    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)

    is_active: Mapped[bool] = mapped_column(nullable=False)
    restitution_time: Mapped[datetime] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="current_lends")
    book: Mapped[Book] = relationship(back_populates="current_lends")

    @classmethod
    def get_or_404(
        cls, lending_id: uuid.UUID, user_id, session: Session
    ) -> Self | None:
        query = select(Lending).where(
            Lending.id == lending_id,
            Lending.user_id == user_id,
        )

        lending = session.execute(query).scalar_one_or_none()

        if not lending:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
            )

        return lending

    @classmethod
    def get_all(
        cls,
        filters: list[ColumnExpressionArgument],
        session: Session,
    ) -> Sequence[Self]:
        """Gets all lendings that fall under specified predicates (``filters``)."""

        query = select(Lending).where(*filters)

        return session.execute(query).scalars().all()

    @classmethod
    def lend_book(
        cls,
        book: Book,
        user_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        session: Session,
    ) -> Self:
        """Lends a book to a user if it is available during a chosen timeframe
        (between ``start_time`` and ``end_time``).

        Each row in this table is linked to one physical book, this means that
        counting rows isn't sufficient to check if there's available stock to lend.

        The book needs to be available during the given dates:
            * start_time < end_time <= any existing start_time
            OR
            * any existing end_time < start_time < end_time
        """
        query = select(Lending).where(
            Lending.book_id == book.id,
            ~or_(
                and_(
                    start_time <= Lending.start_time,
                    end_time <= Lending.start_time,
                ),
                and_(
                    start_time > Lending.end_time,
                    end_time > Lending.end_time,
                ),
            ),
        )
        conflicting_lendings: Sequence[Lending] = session.execute(query).scalars().all()

        if conflicting_lendings:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail={"errors": f"Lending failed for {book.title}: not enough stock"},
            )

        row = cls(
            book_id=book.id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )
        session.add(row)

        return row
