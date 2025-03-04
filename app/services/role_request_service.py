# app/services/role_request_service.py
import logging
from typing import Dict, Any, List

from app.core.auth import create_access_token
from app.core.database import transaction
from app.core.exceptions import ValidationException, ForbiddenException, NotFoundException, DatabaseException
from app.models.role_request import RoleRequest, RoleRequestCreate, RoleRequestStatus, RoleApprovalRequest
from app.models.user import UserUpdate
from app.repositories.role_request_repository import RoleRequestRepository
from app.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class RoleRequestService:
    @staticmethod
    async def create_role_request(user_id: int, requested_role: str, reason: str) -> Dict[str, Any]:
        """새 역할 변경 요청 생성"""
        try:
            # 사용자 존재 확인
            user = await UserRepository.get_by_id(user_id)
            if not user:
                raise NotFoundException(f"ID가 {user_id}인 사용자를 찾을 수 없습니다.")

            # 이미 요청한 역할인지 확인
            if user.role == requested_role:
                raise ValidationException(f"이미 '{requested_role}' 역할을 가지고 있습니다.")

            # 유효한 역할인지 확인
            valid_roles = ["creator", "admin"]
            if requested_role not in valid_roles:
                raise ValidationException(f"유효하지 않은 역할입니다. 가능한 역할: {', '.join(valid_roles)}")

            # 이미 대기 중인 요청이 있는지 확인
            existing_request = await RoleRequestRepository.get_latest_pending_request(user_id)
            if existing_request:
                raise ValidationException("이미 대기 중인 역할 변경 요청이 있습니다.")

            # 새 요청 생성
            request_data = RoleRequestCreate(
                user_id=user_id,
                requested_role=requested_role,
                reason=reason,
                status=RoleRequestStatus.PENDING
            )

            request_id = await RoleRequestRepository.create(request_data)

            logger.info(f"역할 변경 요청 생성: 사용자 ID {user_id}, 요청 역할 {requested_role}, 요청 ID {request_id}")

            return {
                "success": True,
                "request_id": request_id,
                "message": f"역할 변경 요청이 제출되었습니다. 관리자 승인을 기다려주세요."
            }

        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"역할 변경 요청 생성 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_pending_requests(admin_id: int) -> List[Dict[str, Any]]:
        """관리자용 대기 중인 역할 변경 요청 목록 조회"""
        try:
            # 관리자 권한 확인
            admin = await UserRepository.get_by_id(admin_id)
            if not admin or admin.role != "admin":
                raise ForbiddenException("역할 변경 요청 목록을 조회할 권한이 없습니다.")

            # 대기 중인 요청 조회
            requests = await RoleRequestRepository.get_pending_requests()

            # 사용자 정보 포함하여 반환
            result = []
            for req in requests:
                user = await UserRepository.get_by_id(req.user_id)
                if user:
                    result.append({
                        "request_id": req.request_id,
                        "user_id": req.user_id,
                        "username": user.username,
                        "email": user.email,
                        "current_role": user.role,
                        "requested_role": req.requested_role,
                        "reason": req.reason,
                        "create_at": req.create_at  # 변경: created_at → create_at
                    })

            return result

        except ForbiddenException:
            raise
        except Exception as e:
            logger.error(f"대기 중인 역할 변경 요청 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_user_requests(user_id: int) -> List[RoleRequest]:
        """사용자의 역할 변경 요청 내역 조회"""
        try:
            return await RoleRequestRepository.get_user_requests(user_id)
        except Exception as e:
            logger.error(f"사용자 역할 변경 요청 내역 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def approve_role_request(request_id: int, admin_id: int, approval_data: RoleApprovalRequest) -> Dict[
        str, Any]:
        """역할 변경 요청 승인"""
        try:
            # 관리자 권한 확인
            admin = await UserRepository.get_by_id(admin_id)
            if not admin or admin.role != "admin":
                raise ForbiddenException("역할 변경 요청을 승인할 권한이 없습니다.")

            # 요청 존재 확인
            request = await RoleRequestRepository.get_by_id(request_id)
            if not request:
                raise NotFoundException(f"ID가 {request_id}인 역할 변경 요청을 찾을 수 없습니다.")

            # 요청 상태 확인
            if request.status != RoleRequestStatus.PENDING:
                raise ValidationException(f"이미 처리된 요청입니다 (현재 상태: {request.status}).")

            # 사용자 존재 확인
            user = await UserRepository.get_by_id(request.user_id)
            if not user:
                raise NotFoundException(f"ID가 {request.user_id}인 사용자를 찾을 수 없습니다.")

            async with transaction() as conn:
                # 1. 요청 상태 업데이트
                await RoleRequestRepository.update_status(
                    request_id,
                    RoleRequestStatus.APPROVED,
                    admin_id,
                    approval_data.admin_comment,
                    conn
                )

                # 2. 사용자 역할 업데이트
                update_data = UserUpdate(role=request.requested_role)
                await UserRepository.update(request.user_id, update_data, conn)

                # 3. 사용자의 기존 토큰 모두 블랙리스트에 추가 (무효화)
                await TokenBlacklistRepository.blacklist_user_tokens(
                    request.user_id,
                    f"역할이 '{user.role}'에서 '{request.requested_role}'로 변경됨",
                    conn
                )

            # 사용자의 업데이트된 정보 가져오기
            updated_user = await UserRepository.get_by_id(request.user_id)

            # 새 토큰 생성 (업데이트된 역할 정보 포함)
            is_admin = updated_user.is_admin == "Y"
            new_token = create_access_token(
                data={
                    "sub": updated_user.email,
                    "user_id": updated_user.user_id,
                    "is_admin": is_admin,
                    "role": updated_user.role
                }
            )

            logger.info(f"역할 변경 요청 승인: 요청 ID {request_id}, 사용자 ID {request.user_id}, 역할 {request.requested_role}")

            return {
                "success": True,
                "message": f"사용자 '{updated_user.username}'의 역할이 '{request.requested_role}'로 변경되었습니다.",
                "new_token": new_token,
                "user": {
                    "user_id": updated_user.user_id,
                    "email": updated_user.email,
                    "username": updated_user.username,
                    "role": updated_user.role,
                    "is_admin": updated_user.is_admin == "Y"
                }
            }

        except (ValidationException, NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"역할 변경 요청 승인 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def reject_role_request(request_id: int, admin_id: int, rejection_data: RoleApprovalRequest) -> Dict[
        str, Any]:
        """역할 변경 요청 거부"""
        try:
            # 관리자 권한 확인
            admin = await UserRepository.get_by_id(admin_id)
            if not admin or admin.role != "admin":
                raise ForbiddenException("역할 변경 요청을 거부할 권한이 없습니다.")

            # 요청 존재 확인
            request = await RoleRequestRepository.get_by_id(request_id)
            if not request:
                raise NotFoundException(f"ID가 {request_id}인 역할 변경 요청을 찾을 수 없습니다.")

            # 요청 상태 확인
            if request.status != RoleRequestStatus.PENDING:
                raise ValidationException(f"이미 처리된 요청입니다 (현재 상태: {request.status}).")

            # 요청 거부
            await RoleRequestRepository.update_status(
                request_id,
                RoleRequestStatus.REJECTED,
                admin_id,
                rejection_data.admin_comment
            )

            # 사용자 정보 가져오기
            user = await UserRepository.get_by_id(request.user_id)
            username = user.username if user else f"사용자 {request.user_id}"

            logger.info(f"역할 변경 요청 거부: 요청 ID {request_id}, 사용자 ID {request.user_id}")

            return {
                "success": True,
                "message": f"사용자 '{username}'의 역할 변경 요청이 거부되었습니다."
            }

        except (ValidationException, NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"역할 변경 요청 거부 중 오류 발생: {e}")
            raise DatabaseException(str(e))
