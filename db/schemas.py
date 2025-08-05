# db/schemas.py
from pydantic import BaseModel
from typing import Optional

# Schema for creating a new user (input)
class UserCreate(BaseModel):
    email: str
    password: str

# Schema for reading user data (output)
# Note: It does NOT include the password
class User(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True

# Schema for the login response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data stored inside the JWT
class TokenData(BaseModel):
    email: Optional[str] = None