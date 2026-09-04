"""예산 관련 비즈니스 로직. summary가 이 서비스로 예산 사용률/초과 여부를 조회한다."""
from __future__ import annotations

from ..models import validate_amount, validate_month
from ..storage.budget_store import BudgetStore


class BudgetService:
    def __init__(self, budget_store: BudgetStore):
        self.budget_store = budget_store

    def set_budget(self, month: str, amount: int) -> None:
        validate_month(month)
        validate_amount(amount)
        self.budget_store.set(month, amount)

    def get_budget(self, month: str) -> int | None:
        return self.budget_store.get(month)

    def evaluate(self, month: str, total_expense: int) -> dict | None:
        """예산이 설정돼 있으면 사용률(%)과 초과 여부를 계산, 없으면 None."""
        budget = self.get_budget(month)
        if budget is None:
            return None
        usage_rate = (total_expense / budget * 100) if budget > 0 else 0.0
        return {
            "budget": budget,
            "usage_rate": usage_rate,
            "over": total_expense > budget,
        }
