# app/core/exceptions.py
from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    """리소스를 찾을 수 없을 때 발생하는 예외"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class DatabaseException(HTTPException):
    """데이터베이스 관련 예외"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 오류: {detail}"
        )

class ValidationException(HTTPException):
    """입력 데이터 검증 실패 시 발생하는 예외"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class UnauthorizedException(HTTPException):
    """인증 실패 시 발생하는 예외"""
    def __init__(self, detail: str = "인증에 실패했습니다."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class ForbiddenException(HTTPException):
    """권한 없음 예외"""
    def __init__(self, detail: str = "접근 권한이 없습니다."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )