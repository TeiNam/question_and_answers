# app/models/group.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GroupBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    user_id: int  # 그룹 생성자 ID


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupInDB(GroupBase):
    group_id: int
    create_at: datetime
    update_at: datetime


class Group(GroupInDB):
    pass


class GroupMemberBase(BaseModel):
    group_id: int
    user_id: int


class GroupMemberCreate(GroupMemberBase):
    pass


class GroupMemberInDB(GroupMemberBase):
    member_id: int
    create_at: datetime


class GroupMember(GroupMemberInDB):
    pass


class GroupWithMembers(Group):
    members: List[int] = []  # 사용자 ID 목록