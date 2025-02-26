# app/services/category_service.py
import logging
from typing import List, Dict, Any
from fastapi import HTTPException, status
from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.repositories.category_repository import CategoryRepository

logger = logging.getLogger(__name__)


class CategoryService:
    @staticmethod
    async def create_category(category: CategoryCreate) -> Dict[str, Any]:
        """새 카테고리 생성"""
        try:
            category_id = await CategoryRepository.create(category)
            logger.info(f"카테고리 생성 (ID: {category_id}, 이름: {category.name})")

            return {
                "success": True,
                "category_id": category_id,
                "message": "카테고리가 성공적으로 생성되었습니다."
            }
        except Exception as e:
            logger.error(f"카테고리 생성 중 오류 발생: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"카테고리 생성 중 오류 발생: {str(e)}"
            )

    @staticmethod
    async def get_category(category_id: int) -> Category:
        """ID로 카테고리 조회"""
        category = await CategoryRepository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {category_id}인 카테고리를 찾을 수 없습니다."
            )
        return category

    @staticmethod
    async def get_all_categories(is_use: str = None) -> List[Category]:
        """모든 카테고리 조회 (사용 여부 필터링 지원)"""
        if is_use and is_use not in ['Y', 'N']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="is_use 파라미터는 'Y' 또는 'N'이어야 합니다."
            )

        return await CategoryRepository.get_all(is_use=is_use)

    @staticmethod
    async def update_category(
            category_id: int,
            category_update: CategoryUpdate
    ) -> Dict[str, Any]:
        """카테고리 업데이트"""
        # 카테고리 존재 여부 확인
        category = await CategoryRepository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {category_id}인 카테고리를 찾을 수 없습니다."
            )

        # 카테고리 업데이트
        success = await CategoryRepository.update(category_id, category_update)

        # 로그 기록
        logger.info(f"카테고리 업데이트 (ID: {category_id}) - 필드: {', '.join(category_update.dict(exclude_unset=True).keys())}")

        return {
            "success": success,
            "message": "카테고리가 성공적으로 업데이트되었습니다."
        }

    @staticmethod
    async def delete_category(category_id: int) -> Dict[str, Any]:
        """카테고리 삭제"""
        # 카테고리 존재 여부 확인
        category = await CategoryRepository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {category_id}인 카테고리를 찾을 수 없습니다."
            )

        # TODO: 카테고리를 참조하는 질문이 있는지 확인하는 로직 추가 필요
        # 이 부분은 비즈니스 요구사항에 따라 다를 수 있음
        # 예: 참조 중인 질문이 있으면 삭제 방지 또는 해당 질문들도 함께 삭제

        # 카테고리 삭제
        success = await CategoryRepository.delete(category_id)

        # 로그 기록
        logger.info(f"카테고리 삭제 (ID: {category_id})")

        return {
            "success": success,
            "message": "카테고리가 성공적으로 삭제되었습니다."
        }