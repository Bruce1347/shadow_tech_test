from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.books import BookDumpSchema


class LendingSchema(BaseModel):
    start_time: datetime
    end_time: datetime
    is_active: bool = True


class LendingEditSchema(BaseModel):
    end_time: datetime
    is_active: bool = True


class LendingDumpSchema(BaseModel):
    id: UUID
    book: BookDumpSchema
    user_id: UUID
    start_time: datetime
    end_time: datetime
    is_active: bool
    return_time: datetime | None

    model_config = ConfigDict(from_attributes=True)
