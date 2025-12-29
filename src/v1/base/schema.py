from typing import (
    Any,
    Optional,
)
from pydantic import BaseModel, ConfigDict


class BaseAPISchema(BaseModel):
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseAPISchema):
    status: str = "error"
    error_code: Optional[str] = None
    resolution: Optional[str] = None


class SuccessResponse(BaseAPISchema):
    status: str = "success"


#constant messages
