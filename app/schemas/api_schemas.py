import typing

from pydantic import BaseModel


class BaseResponse(BaseModel):
    result: typing.Any
    error: bool = False

class AddUserBody(BaseModel):
    user_id: int
    username: str

    first_name: str
    last_name: str
    photo_url: str