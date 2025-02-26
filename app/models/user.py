# app/models/user.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str):
    ADMIN = "admin"      # 관리자
    CREATOR = "creator"  # 출제자
    SOLVER = "solver"    # 풀이자


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    is_active: str = "Y"
    is_admin: str = "N"
    role: str = UserRole.SOLVER  # 기본값은 풀이자


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[str] = None
    is_admin: Optional[str] = None
    role: Optional[str] = None


class UserInDB(UserBase):
    user_id: int
    is_active: str
    is_admin: str
    role: str
    create_at: datetime
    update_at: datetime


class User(UserInDB):
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str