from pydantic import BaseModel, ConfigDict


class AuthorSchema(BaseModel):
    first_name: str
    last_name: str


class AuthorDumpSchema(AuthorSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BookSchema(BaseModel):
    title: str
    author_id: int

    # Optional fields
    isbn: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookDumpSchema(BookSchema):
    id: int
    author: AuthorDumpSchema
    available: bool

    model_config = ConfigDict(from_attributes=True)
