from pydantic import BaseModel


class RootResponse(BaseModel):
    name: str
    message: str
    version: str
    docs: str
    health: str


class ErrorResponse(BaseModel):
    detail: str
