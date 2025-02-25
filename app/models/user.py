# app/models/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    is_active: str = "Y"
    is_admin: str = "N"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[str] = None
    is_admin: Optional[str] = None


class UserInDB(UserBase):
    user_id: int
    is_active: str
    is_admin: str
    create_at: datetime
    update_at: datetime


class User(UserInDB):
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str