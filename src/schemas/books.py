from pydantic import BaseModel, ConfigDict, Field


class AuthorSchema(BaseModel):
    first_name: str
    last_name: str


class AuthorDumpSchema(AuthorSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BookSchema(BaseModel):
    title: str
    author_id: int
    total_stock: int | None = 0

    # Optional fields
    isbn: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookDumpSchema(BookSchema):
    author: AuthorDumpSchema
    available: int = 0
    borrowed: int = 0
