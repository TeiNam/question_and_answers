# app/services/group_service.py
import logging
from typing import List, Dict, Any

from app.core.exceptions import NotFoundException, ForbiddenException, DatabaseException
from app.models.group import Group, GroupCreate, GroupUpdate, GroupMemberCreate
from app.repositories.group_repository import GroupRepository, GroupMemberRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class GroupService:
    @staticmethod
    async def create_group(group: GroupCreate) -> Dict[str, Any]:
        """새 그룹 생성"""
        try:
            # 사용자 존재 및 출제자 권한 확인
            user = await UserRepository.get_by_id(group.user_id)
            if not user:
                raise NotFoundException(f"ID가 {group.user_id}인 사용자를 찾을 수 없습니다.")

            if user.role != "creator" and user.role != "admin":
                raise ForbiddenException("그룹 생성 권한이 없습니다. 출제자 또는 관리자만 그룹을 생성할 수 있습니다.")

            # 그룹 생성
            group_id = await GroupRepository.create_group(group)
            logger.info(f"그룹 생성 (ID: {group_id}, 이름: {group.name}, 출제자: {group.user_id})")

            return {
                "success": True,
                "group_id": group_id,
                "message": "그룹이 성공적으로 생성되었습니다."
            }
        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"그룹 생성 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_group(group_id: int) -> Dict[str, Any]:
        """그룹 상세 정보 조회"""
        group_with_members = await GroupRepository.get_group_with_members(group_id)
        if not group_with_members:
            raise NotFoundException(f"ID가 {group_id}인 그룹을 찾을 수 없습니다.")
        return group_with_members

    @staticmethod
    async def update_group(group_id: int, group_update: GroupUpdate, user_id: int) -> Dict[str, Any]:
        """그룹 정보 업데이트"""
        try:
            # 그룹 존재 여부 및 소유권 확인
            group = await GroupRepository.get_by_id(group_id)
            if not group:
                raise NotFoundException(f"ID가 {group_id}인 그룹을 찾을 수 없습니다.")

            user = await UserRepository.get_by_id(user_id)
            if group.user_id != user_id and user.role != "admin":
                raise ForbiddenException("해당 그룹을 수정할 권한이 없습니다.")

            # 그룹 업데이트
            success = await GroupRepository.update(group_id, group_update)

            return {
                "success": success,
                "message": "그룹 정보가 성공적으로 업데이트되었습니다."
            }
        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"그룹 업데이트 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def delete_group(group_id: int, user_id: int) -> Dict[str, Any]:
        """그룹 삭제"""
        try:
            # 그룹 존재 여부 및 소유권 확인
            group = await GroupRepository.get_by_id(group_id)
            if not group:
                raise NotFoundException(f"ID가 {group_id}인 그룹을 찾을 수 없습니다.")

            user = await UserRepository.get_by_id(user_id)
            if group.user_id != user_id and user.role != "admin":
                raise ForbiddenException("해당 그룹을 삭제할 권한이 없습니다.")

            # 그룹 삭제
            success = await GroupRepository.delete(group_id)

            return {
                "success": success,
                "message": "그룹이 성공적으로 삭제되었습니다."
            }
        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"그룹 삭제 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def add_member(group_id: int, user_id: int, added_by_id: int) -> Dict[str, Any]:
        """그룹에 멤버 추가"""
        try:
            # 그룹 존재 여부 및 권한 확인
            group = await GroupRepository.get_by_id(group_id)
            if not group:
                raise NotFoundException(f"ID가 {group_id}인 그룹을 찾을 수 없습니다.")

            adding_user = await UserRepository.get_by_id(added_by_id)
            if group.user_id != added_by_id and adding_user.role != "admin":
                raise ForbiddenException("그룹에 멤버를 추가할 권한이 없습니다.")

            # 추가할 사용자 존재 확인
            member = await UserRepository.get_by_id(user_id)
            if not member:
                raise NotFoundException(f"ID가 {user_id}인 사용자를 찾을 수 없습니다.")

            # 이미 멤버인지 확인
            is_member = await GroupMemberRepository.is_member(group_id, user_id)
            if is_member:
                return {
                    "success": False,
                    "message": "해당 사용자는 이미 그룹의 멤버입니다."
                }

            # 멤버 추가
            member_data = GroupMemberCreate(group_id=group_id, user_id=user_id)
            member_id = await GroupMemberRepository.add_member(member_data)

            return {
                "success": True,
                "member_id": member_id,
                "message": "멤버가 성공적으로 추가되었습니다."
            }
        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"그룹에 멤버 추가 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def remove_member(group_id: int, user_id: int, removed_by_id: int) -> Dict[str, Any]:
        """그룹에서 멤버 제거"""
        try:
            # 그룹 존재 여부 및 권한 확인
            group = await GroupRepository.get_by_id(group_id)
            if not group:
                raise NotFoundException(f"ID가 {group_id}인 그룹을 찾을 수 없습니다.")

            removing_user = await UserRepository.get_by_id(removed_by_id)
            if group.user_id != removed_by_id and removing_user.role != "admin" and removed_by_id != user_id:
                raise ForbiddenException("그룹에서 멤버를 제거할 권한이 없습니다.")

            # 멤버인지 확인
            is_member = await GroupMemberRepository.is_member(group_id, user_id)
            if not is_member:
                return {
                    "success": False,
                    "message": "해당 사용자는 그룹의 멤버가 아닙니다."
                }

            # 멤버 제거
            success = await GroupMemberRepository.remove_member(group_id, user_id)

            return {
                "success": success,
                "message": "멤버가 성공적으로 제거되었습니다."
            }
        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"그룹에서 멤버 제거 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_user_groups(user_id: int) -> List[Group]:
        """사용자가 속한 그룹 목록 조회"""
        try:
            return await GroupRepository.get_groups_by_member(user_id)
        except Exception as e:
            logger.error(f"사용자의 그룹 목록 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_creator_groups(user_id: int) -> List[Group]:
        """출제자가 생성한 그룹 목록 조회"""
        try:
            return await GroupRepository.get_groups_by_creator(user_id)
        except Exception as e:
            logger.error(f"출제자의 그룹 목록 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))