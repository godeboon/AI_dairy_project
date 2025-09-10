from pydantic import BaseModel

class MessageInput(BaseModel):
    message: str

class TurnInput(BaseModel):
    turn: int
