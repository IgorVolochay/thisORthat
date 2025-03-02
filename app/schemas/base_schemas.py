from pydantic import BaseModel

class User(BaseModel):
    user_id: int
    username: str

    first_name: str
    last_name: str
    photo_url: str

    activity: int = 0
    liked_card_ids: list[int] = list()
    disliked_card_ids: list[int] = list()
    comments_ids: list[int] = list()

    registration_date: str

class Visited(BaseModel):
    user_id: int
    cards_visited: set[int]

class Card(BaseModel):
    card_id: int

    choice_A: str
    choice_B: str

    count_choice_A: int = 0
    count_choice_B: int = 0
    count_total: int = 0

    count_likes: int = 0
    count_dislikes: int = 0
    comments: list[int] = list()

    author_id: int
    creation_date: str
    moderation_date: str = "Not moderated"
    active_status: bool = False