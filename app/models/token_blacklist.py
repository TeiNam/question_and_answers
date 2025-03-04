# app/models/token_blacklist.py
from datetime import datetime

from pydantic import BaseModel


class TokenBlacklistBase(BaseModel):
    user_id: int
    jti: str  # JWT token ID
    reason: str


class TokenBlacklistCreate(TokenBlacklistBase):
    expire_at: datetime  # 변경: expires_at → expire_at


class TokenBlacklistInDB(TokenBlacklistBase):
    id: int
    create_at: datetime  # 변경: created_at → create_at
    expire_at: datetime  # 변경: expires_at → expire_at


class TokenBlacklist(TokenBlacklistInDB):
    pass
