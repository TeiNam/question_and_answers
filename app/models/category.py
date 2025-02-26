# app/models/category.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    is_use: str = Field("Y", regex='^[YN]$')  # "Y" 또는 "N"만 허용


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    is_use: Optional[str] = None


class CategoryInDB(CategoryBase):
    category_id: int
    create_at: datetime
    update_at: datetime


class Category(CategoryInDB):
    pass