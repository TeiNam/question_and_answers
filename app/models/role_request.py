# app/models/role_request.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RoleRequestStatus(str):
    PENDING = "pending"  # 대기 중
    APPROVED = "approved"  # 승인됨
    REJECTED = "rejected"  # 거부됨


class RoleRequestBase(BaseModel):
    user_id: int
    requested_role: str = Field(..., description="요청 역할 (creator, admin 등)")
    reason: str = Field(..., description="요청 사유")


class RoleRequestCreate(RoleRequestBase):
    status: str = RoleRequestStatus.PENDING


class RoleRequestUpdate(BaseModel):
    status: str
    processed_by: Optional[int] = None
    process_at: Optional[datetime] = None  # 변경: processed_at → process_at
    admin_comment: Optional[str] = None


class RoleRequestInDB(RoleRequestBase):
    request_id: int
    status: str
    create_at: datetime  # 변경: created_at → create_at
    processed_by: Optional[int] = None
    process_at: Optional[datetime] = None  # 변경: processed_at → process_at
    admin_comment: Optional[str] = None


class RoleRequest(RoleRequestInDB):
    pass


class RoleApprovalRequest(BaseModel):
    admin_comment: Optional[str] = None