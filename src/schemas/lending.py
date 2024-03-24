from pydantic import BaseModel, ConfigDict
from uuid import UUID
from src.schemas.books import BookDumpSchema
from datetime import datetime


class LendingSchema(BaseModel):
    start_time: datetime
    end_time: datetime

class LendingDumpSchema(BaseModel):
    id: UUID
    book: BookDumpSchema
    user_id: UUID
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)
