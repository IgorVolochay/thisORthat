import typing

from pydantic import BaseModel


class BaseResponse(BaseModel):
    result: typing.Any
    error: bool = False
