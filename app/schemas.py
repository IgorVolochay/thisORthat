from pydantic import BaseModel


class User(BaseModel):
    user_id: int
    username: str

    first_name: str
    last_name: str
    photo_path: str

    activity: int = 0
    liked_post_ids: list[int] = None
    disliked_post_ids: list[int] = None
    comments_ids: list[int] = None

    registration_date: str
