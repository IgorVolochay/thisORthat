import typing

from pydantic import BaseModel, NonNegativeInt

from typing import Optional


class BaseResponse(BaseModel):
    result: typing.Any
    error: bool = False

class AddUserBody(BaseModel):
    user_id: Optional[NonNegativeInt] = None
    username: str

    first_name: str
    last_name: str
    photo_url: str

class AddCardBody(BaseModel):
    choice_A: str
    choice_B: str

    author_id: Optional[NonNegativeInt] = None

class SelectChoice(BaseModel):
    user_id: Optional[NonNegativeInt] = None
    card_id: NonNegativeInt

    choice: typing.Literal["A", "B"]

class ReactionCard(BaseModel):
    user_id: Optional[NonNegativeInt] = None
    card_id: NonNegativeInt

class AddCommentBody(BaseModel):
    author_id: Optional[NonNegativeInt] = None
    card_id: NonNegativeInt

    comment_text: str