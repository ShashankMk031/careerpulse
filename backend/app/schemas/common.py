from typing import Generic, TypeVar, Any
from pydantic import BaseModel

DataType = TypeVar('DataType')

class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    has_next: bool
    has_previous: bool

class ResponseEnvelope(BaseModel, Generic[DataType]):
    success: bool = True
    data: DataType
    metadata: Any | None = None

class ErrorEnvelope(BaseModel):
    success: bool = False
    error: str
    error_code: str
