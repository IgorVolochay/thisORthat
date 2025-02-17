import typing

from pydantic import BaseModel


class User(BaseModel):
    user_id: int
    username: str

    first_name: str
    last_name: str
    photo_id: str

    activity: int = 0
    liked_post_ids: list[int] = list()
    disliked_post_ids: list[int] = list()
    comments_ids: list[int] = list()

    registration_date: str

class BaseResponse(BaseModel):
    result: typing.Any
    error: bool = False
