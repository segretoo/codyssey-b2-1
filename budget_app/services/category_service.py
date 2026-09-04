"""카테고리 관련 비즈니스 로직. 삭제 시 참조 무결성(사용 중 여부)을 검사한다."""
from __future__ import annotations

from ..exceptions import CategoryInUseError
from ..storage.category_store import CategoryStore
from .transaction_service import TransactionService


class CategoryService:
    def __init__(self, category_store: CategoryStore, transaction_service: TransactionService):
        self.category_store = category_store
        self.transaction_service = transaction_service

    def list_all(self) -> list[str]:
        return self.category_store.list_all()

    def exists(self, name: str) -> bool:
        return self.category_store.exists(name)

    def add(self, name: str) -> None:
        self.category_store.add(name)

    def remove(self, name: str) -> None:
        if self.transaction_service.is_category_in_use(name):
            raise CategoryInUseError(
                f"사용 중인 카테고리는 삭제할 수 없습니다: {name} (해당 거래를 먼저 정리하세요)"
            )
        self.category_store.remove(name)
