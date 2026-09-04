"""--datadir 경로를 받아 storage/service 객체들을 조립하는 조립 지점."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..services.budget_service import BudgetService
from ..services.category_service import CategoryService
from ..services.recurring_service import RecurringService
from ..services.transaction_service import TransactionService
from ..storage.budget_store import BudgetStore
from ..storage.category_store import CategoryStore
from ..storage.recurring_store import RecurringStore
from ..storage.transaction_repository import TransactionRepository


@dataclass
class AppContext:
    datadir: Path
    transaction_service: TransactionService
    category_service: CategoryService
    budget_service: BudgetService
    recurring_service: RecurringService


def build_context(datadir: str) -> AppContext:
    base = Path(datadir)

    tx_repo = TransactionRepository(base / "transactions.jsonl")
    category_store = CategoryStore(base / "categories.jsonl")
    budget_store = BudgetStore(base / "budgets.jsonl")
    recurring_store = RecurringStore(base / "recurring.jsonl")

    tx_service = TransactionService(tx_repo, category_store)
    category_service = CategoryService(category_store, tx_service)
    budget_service = BudgetService(budget_store)
    recurring_service = RecurringService(recurring_store, tx_service)

    return AppContext(
        datadir=base,
        transaction_service=tx_service,
        category_service=category_service,
        budget_service=budget_service,
        recurring_service=recurring_service,
    )
