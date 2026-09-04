"""
반복 거래(월급/월세 등) 규칙 관리 + 특정 월에 실제 거래로 생성 (보너스 2번).

중복 생성 방지: 생성된 거래에는 'recurring:<rule_id>' 태그를 남겨두고,
generate_for_month 호출 시 해당 월에 이미 그 태그가 있으면 다시 만들지 않는다.
"""
from __future__ import annotations

from ..exceptions import ValidationError
from ..models import (
    RecurringRule,
    validate_amount,
    validate_day_of_month,
    validate_month,
    validate_type,
)
from ..storage.recurring_store import RecurringStore
from .transaction_service import TransactionService

RECURRING_TAG_PREFIX = "recurring:"


class RecurringService:
    def __init__(self, store: RecurringStore, transaction_service: TransactionService):
        self.store = store
        self.transaction_service = transaction_service

    def add(
        self,
        day_of_month: int,
        type_: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> RecurringRule:
        validate_day_of_month(day_of_month)
        tx_type = validate_type(type_)
        validate_amount(amount)
        if not self.transaction_service.category_store.exists(category):
            raise ValidationError(f"등록되지 않은 카테고리입니다: {category}")

        rule = RecurringRule(
            id=self.store.next_id(),
            day_of_month=day_of_month,
            type=tx_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags or [],
        )
        self.store.append(rule)
        return rule

    def list_all(self) -> list[RecurringRule]:
        return list(self.store.stream_all())

    def remove(self, rule_id: str) -> None:
        self.store.delete(rule_id)

    def generate_for_month(self, month: str) -> tuple[int, int]:
        """month(YYYY-MM)에 등록된 모든 규칙으로 거래를 생성한다. 이미 생성된 건 건너뛴다."""
        validate_month(month)

        existing = self.transaction_service.search(date_from=f"{month}-01", date_to=f"{month}-31")
        already_done = {
            tag[len(RECURRING_TAG_PREFIX):]
            for tx in existing
            for tag in tx.tags
            if tag.startswith(RECURRING_TAG_PREFIX)
        }

        created = 0
        skipped = 0
        for rule in self.store.stream_all():
            if rule.id in already_done:
                skipped += 1
                continue
            date = f"{month}-{rule.day_of_month:02d}"
            self.transaction_service.add(
                date=date,
                type_=rule.type.value,
                category=rule.category,
                amount=rule.amount,
                memo=rule.memo,
                tags=[*rule.tags, f"{RECURRING_TAG_PREFIX}{rule.id}"],
            )
            created += 1
        return created, skipped
