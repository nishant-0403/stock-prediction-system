from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    telegram_id: int | None = None

