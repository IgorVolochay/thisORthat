import typing

from pydantic import BaseModel, NonNegativeInt


class BaseResponse(BaseModel):
    result: typing.Any
    error: bool = False

class AddUserBody(BaseModel):
    user_id: NonNegativeInt
    username: str

    first_name: str
    last_name: str
    photo_url: str

class AddCardBody(BaseModel):
    choice_A: str
    choice_B: str

    author_id: NonNegativeInt