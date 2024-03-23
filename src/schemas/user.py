from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    first_name: str | None
    last_name: str | None
    username: str
    address: str | None
    email: str


class UserCreationSchema(UserSchema):
    password: str

class UserDumpSchema(UserSchema):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
