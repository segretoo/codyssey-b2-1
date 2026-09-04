"""거래 관련 비즈니스 로직. CLI는 이 서비스만 호출하고 storage를 직접 건드리지 않는다."""
from __future__ import annotations

import csv
import heapq
from typing import Optional

from ..exceptions import ValidationError
from ..models import Transaction, TransactionType, validate_amount, validate_date, validate_type
from ..storage.category_store import CategoryStore
from ..storage.transaction_repository import TransactionRepository
from ..utils import parse_tags


class TransactionService:
    def __init__(self, repo: TransactionRepository, category_store: CategoryStore):
        self.repo = repo
        self.category_store = category_store

    def add(
        self,
        date: str,
        type_: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: Optional[list[str]] = None,
    ) -> Transaction:
        validate_date(date)
        tx_type = validate_type(type_)
        validate_amount(amount)
        if not self.category_store.exists(category):
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {category} (category add로 먼저 등록하세요)"
            )
        tx = Transaction(
            id=self.repo.next_id(),
            date=date,
            type=tx_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags or [],
        )
        self.repo.append(tx)
        return tx

    def list_recent(self, limit: int = 20) -> list[Transaction]:
        """
        heapq.nlargest로 상위 limit개만 메모리에 유지한 채 스트림을 순회한다.
        (list(...)+sort()로 전체를 리스트로 모으지 않으므로, 메모리 사용량이
        전체 레코드 수가 아니라 limit 크기에 비례한다.)
        """
        return heapq.nlargest(limit, self.repo.stream_all(), key=lambda t: (t.date, t.id))

    def search(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        type_: Optional[str] = None,
        query: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[Transaction]:
        results: list[Transaction] = []
        for tx in self.repo.stream_all():  # 조건에 안 맞는 건 즉시 버리고 다음 줄로
            if date_from and tx.date < date_from:
                continue
            if date_to and tx.date > date_to:
                continue
            if category and tx.category != category:
                continue
            if type_ and tx.type.value != type_:
                continue
            if query and query not in (tx.memo or ""):
                continue
            if tag and tag not in tx.tags:
                continue
            results.append(tx)
        results.sort(key=lambda t: (t.date, t.id), reverse=True)
        return results

    def summary(self, month: str, top_n: int = 3) -> dict:
        total_income = 0
        total_expense = 0
        category_expense: dict[str, int] = {}
        found_any = False

        for tx in self.repo.stream_all():
            if not tx.date.startswith(month):
                continue
            found_any = True
            if tx.type == TransactionType.INCOME:
                total_income += tx.amount
            else:
                total_expense += tx.amount
                category_expense[tx.category] = category_expense.get(tx.category, 0) + tx.amount

        top_categories = sorted(category_expense.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        return {
            "found_any": found_any,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
        }

    def update(self, tx_id: str, **fields) -> Transaction:
        if fields.get("date") is not None:
            validate_date(fields["date"])
        if fields.get("type") is not None:
            fields["type"] = validate_type(fields["type"])
        if fields.get("amount") is not None:
            validate_amount(fields["amount"])
        if fields.get("category") is not None and not self.category_store.exists(fields["category"]):
            raise ValidationError(f"등록되지 않은 카테고리입니다: {fields['category']}")
        if isinstance(fields.get("tags"), str):
            fields["tags"] = parse_tags(fields["tags"])

        def updater(tx: Transaction) -> Transaction:
            for key, value in fields.items():
                if value is not None:
                    setattr(tx, key, value)
            return tx

        return self.repo.update(tx_id, updater)

    def delete(self, tx_id: str) -> None:
        self.repo.delete(tx_id)

    def is_category_in_use(self, category: str) -> bool:
        return self.repo.is_category_in_use(category)

    def export_csv(
        self,
        out_path: str,
        month: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> int:
        rows = self.search(date_from=date_from, date_to=date_to)
        if month:
            rows = [tx for tx in rows if tx.date.startswith(month)]

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])
            for tx in rows:
                writer.writerow([tx.date, tx.type.value, tx.category, tx.amount, tx.memo, ",".join(tx.tags)])
        return len(rows)

    def import_csv(self, csv_path: str) -> tuple[int, int]:
        imported = 0
        skipped = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    self.add(
                        date=row["date"],
                        type_=row["type"],
                        category=row["category"],
                        amount=int(row["amount"]),
                        memo=row.get("memo", "") or "",
                        tags=parse_tags(row.get("tags", "")),
                    )
                    imported += 1
                except (ValidationError, KeyError, ValueError):
                    skipped += 1
        return imported, skipped
