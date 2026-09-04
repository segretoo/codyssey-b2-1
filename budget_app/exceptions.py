class BudgetAppError(Exception):
    """앱 전역 기본 예외. 모든 커스텀 예외는 이걸 상속받는다."""


class ValidationError(BudgetAppError):
    """입력 검증 실패 (날짜 형식, 음수 금액, 잘못된 type/category 등)."""


class NotFoundError(BudgetAppError):
    """존재하지 않는 id/카테고리 등을 조회·수정·삭제하려 할 때."""


class CategoryInUseError(BudgetAppError):
    """사용 중인 카테고리를 삭제하려 할 때."""


class StorageError(BudgetAppError):
    """파일 I/O 관련 오류 (쓰기 실패, 손상된 레코드 등)."""
