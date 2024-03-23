from sqlalchemy import ForeignKey, Integer, String, delete, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

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
    def exists(cls, author_id: int, session) -> bool:
        return session.query(select(cls).where(cls.id == author_id).exists()).scalar()

    @classmethod
    def get(cls, author_id: int, session: Session) -> "Author | None":
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
    def get_authors_list(cls, session: Session) -> list["Author"]:
        query = session.query(cls)

        return session.execute(query).scalars().fetchall()

    @classmethod
    def create_object(cls, validated_data: AuthorSchema, session: Session):
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

    total_stock: Mapped[int] = mapped_column(Integer())

    @classmethod
    def get(cls, book_id: int, session: Session) -> "Book | None":
        return session.execute(session.query(cls).filter(cls.id == book_id)).scalar()

    @classmethod
    def get_all(cls, session: Session) -> "list[Book]":
        return session.execute(session.query(cls)).scalars()

    @classmethod
    def create(cls, validated_data: BookSchema, session: Session):
        instance = cls(**validated_data.model_dump())

        session.add(instance)

        return instance

    @classmethod
    def exists(cls, book_id: int, session) -> bool:
        return session.query(select(cls).where(cls.id == book_id).exists()).scalar()

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

    @property
    def password(self):
        return self.hashed_password

    @password.setter
    def password(self, new_password):
        context = CryptContext(schemes=["bcrypt"])
        self.hashed_password = context.hash(new_password)

    @classmethod
    def create(cls, validated_data: UserSchema, session: Session):
        instance = cls(**validated_data.model_dump())
        session.add(instance)
        return instance

