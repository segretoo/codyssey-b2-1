"""
budget_app 핵심 로직에 대한 자동화 테스트.
표준 라이브러리 unittest만 사용 (pip install 불필요).

실행:
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from budget_app.exceptions import CategoryInUseError, NotFoundError, ValidationError
from budget_app.services.budget_service import BudgetService
from budget_app.services.category_service import CategoryService
from budget_app.services.recurring_service import RecurringService
from budget_app.services.transaction_service import TransactionService
from budget_app.storage.budget_store import BudgetStore
from budget_app.storage.category_store import CategoryStore
from budget_app.storage.recurring_store import RecurringStore
from budget_app.storage.transaction_repository import TransactionRepository
from budget_app.utils import format_table


class BudgetAppTestCase(unittest.TestCase):
    """테스트마다 임시 폴더를 새로 만들어 완전히 독립된 데이터로 실행한다."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        base = Path(self.tmp_dir)

        self.tx_repo = TransactionRepository(base / "transactions.jsonl")
        self.category_store = CategoryStore(base / "categories.jsonl")
        self.budget_store = BudgetStore(base / "budgets.jsonl")

        self.recurring_store = RecurringStore(base / "recurring.jsonl")

        self.tx_service = TransactionService(self.tx_repo, self.category_store)
        self.category_service = CategoryService(self.category_store, self.tx_service)
        self.budget_service = BudgetService(self.budget_store)
        self.recurring_service = RecurringService(self.recurring_store, self.tx_service)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ---- 카테고리 기본값 ----

    def test_default_categories_are_created(self):
        names = self.category_service.list_all()
        self.assertIn("food", names)
        self.assertIn("salary", names)

    # ---- add ----

    def test_add_and_list(self):
        self.tx_service.add(date="2024-01-15", type_="expense", category="food", amount=15000, memo="점심")
        rows = self.tx_service.list_recent(limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, 15000)
        self.assertEqual(rows[0].id, "TX-000001")  # id가 1부터 자동 채번되는지

    def test_add_rejects_negative_amount(self):
        with self.assertRaises(ValidationError):
            self.tx_service.add(date="2024-01-15", type_="expense", category="food", amount=-1000)

    def test_add_rejects_invalid_date(self):
        with self.assertRaises(ValidationError):
            self.tx_service.add(date="2024-13-40", type_="expense", category="food", amount=1000)

    def test_add_rejects_unknown_category(self):
        with self.assertRaises(ValidationError):
            self.tx_service.add(date="2024-01-15", type_="expense", category="없는카테고리", amount=1000)

    # ---- search ----

    def test_search_filters_by_category_and_sorts_latest_first(self):
        self.tx_service.add(date="2024-01-10", type_="expense", category="food", amount=1000)
        self.tx_service.add(date="2024-01-20", type_="expense", category="food", amount=2000)
        self.tx_service.add(date="2024-01-15", type_="expense", category="transport", amount=3000)

        results = self.tx_service.search(category="food")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].date, "2024-01-20")  # 최신순 정렬 확인

    # ---- update / delete ----

    def test_update_changes_fields(self):
        tx = self.tx_service.add(date="2024-01-15", type_="expense", category="food", amount=1000)
        updated = self.tx_service.update(tx.id, amount=5000, memo="수정됨")
        self.assertEqual(updated.amount, 5000)
        self.assertEqual(updated.memo, "수정됨")

    def test_update_nonexistent_id_raises(self):
        with self.assertRaises(NotFoundError):
            self.tx_service.update("TX-999999", amount=1000)

    def test_delete_removes_transaction(self):
        tx = self.tx_service.add(date="2024-01-15", type_="expense", category="food", amount=1000)
        self.tx_service.delete(tx.id)
        self.assertEqual(len(self.tx_service.list_recent()), 0)

    def test_delete_nonexistent_id_raises(self):
        with self.assertRaises(NotFoundError):
            self.tx_service.delete("TX-999999")

    # ---- summary / budget ----

    def test_summary_totals_and_top_categories(self):
        self.tx_service.add(date="2024-01-01", type_="income", category="salary", amount=3_000_000)
        self.tx_service.add(date="2024-01-05", type_="expense", category="food", amount=45_000)
        self.tx_service.add(date="2024-01-06", type_="expense", category="rent", amount=150_000)
        self.tx_service.add(date="2024-01-07", type_="expense", category="transport", amount=20_000)

        result = self.tx_service.summary(month="2024-01", top_n=3)
        self.assertEqual(result["total_income"], 3_000_000)
        self.assertEqual(result["total_expense"], 215_000)
        self.assertEqual(result["balance"], 2_785_000)
        self.assertEqual(result["top_categories"][0], ("rent", 150_000))  # 지출 1위 확인

    def test_budget_usage_rate(self):
        self.tx_service.add(date="2024-01-05", type_="expense", category="food", amount=250_000)
        self.budget_service.set_budget("2024-01", 500_000)

        result = self.tx_service.summary(month="2024-01")
        evaluation = self.budget_service.evaluate("2024-01", result["total_expense"])

        self.assertAlmostEqual(evaluation["usage_rate"], 50.0)
        self.assertFalse(evaluation["over"])

    # ---- category 참조 무결성 ----

    def test_cannot_remove_category_in_use(self):
        self.tx_service.add(date="2024-01-15", type_="expense", category="food", amount=1000)
        with self.assertRaises(CategoryInUseError):
            self.category_service.remove("food")

    def test_can_remove_unused_category(self):
        self.category_service.remove("etc")
        self.assertNotIn("etc", self.category_service.list_all())

    # ---- 대량 데이터에서도 정상 동작하는지 (스트리밍 확인용) ----

    def test_handles_many_transactions(self):
        for i in range(200):
            day = (i % 28) + 1
            self.tx_service.add(
                date=f"2024-02-{day:02d}", type_="expense", category="food", amount=1000 + i
            )
        result = self.tx_service.summary(month="2024-02")
        self.assertEqual(result["total_expense"], sum(1000 + i for i in range(200)))


    # ---- category_service.exists (add 재입력/등록 유도 흐름이 의존하는 부분) ----

    def test_category_service_exists(self):
        self.assertTrue(self.category_service.exists("food"))
        self.assertFalse(self.category_service.exists("없는카테고리"))

    # ---- 보너스 2: 반복 내역 ----

    def test_recurring_add_and_list(self):
        rule = self.recurring_service.add(
            day_of_month=25, type_="income", category="salary", amount=3_000_000
        )
        self.assertEqual(rule.id, "RC-000001")
        rules = self.recurring_service.list_all()
        self.assertEqual(len(rules), 1)

    def test_recurring_add_rejects_invalid_day(self):
        with self.assertRaises(ValidationError):
            self.recurring_service.add(day_of_month=31, type_="expense", category="rent", amount=1000)

    def test_recurring_generate_creates_transactions(self):
        self.recurring_service.add(day_of_month=25, type_="income", category="salary", amount=3_000_000)
        self.recurring_service.add(day_of_month=1, type_="expense", category="rent", amount=500_000)

        created, skipped = self.recurring_service.generate_for_month("2024-03")
        self.assertEqual(created, 2)
        self.assertEqual(skipped, 0)

        rows = self.tx_service.search(date_from="2024-03-01", date_to="2024-03-31")
        self.assertEqual(len(rows), 2)
        dates = sorted(tx.date for tx in rows)
        self.assertEqual(dates, ["2024-03-01", "2024-03-25"])

    def test_recurring_generate_is_idempotent(self):
        """같은 달에 두 번 generate해도 중복 생성되지 않아야 한다."""
        self.recurring_service.add(day_of_month=25, type_="income", category="salary", amount=3_000_000)

        created1, skipped1 = self.recurring_service.generate_for_month("2024-03")
        created2, skipped2 = self.recurring_service.generate_for_month("2024-03")

        self.assertEqual((created1, skipped1), (1, 0))
        self.assertEqual((created2, skipped2), (0, 1))
        rows = self.tx_service.search(date_from="2024-03-01", date_to="2024-03-31")
        self.assertEqual(len(rows), 1)  # 두 번 실행해도 1건만 있어야 함

    def test_recurring_remove(self):
        rule = self.recurring_service.add(day_of_month=1, type_="expense", category="rent", amount=1000)
        self.recurring_service.remove(rule.id)
        self.assertEqual(self.recurring_service.list_all(), [])

    def test_recurring_remove_nonexistent_raises(self):
        with self.assertRaises(NotFoundError):
            self.recurring_service.remove("RC-999999")

    # ---- 보너스 3: 콘솔 테이블 포맷 ----

    def test_format_table_aligns_columns(self):
        text = format_table(["id", "금액"], [["TX-000001", 1000], ["TX-000002", 2000]])
        lines = text.splitlines()
        self.assertEqual(len(lines), 4)  # 헤더 + 구분선 + 데이터 2줄
        # 헤더 아래 구분선이 '-'로만 구성되는지
        self.assertTrue(set(lines[1].replace(" ", "")) <= {"-"})

    def test_format_table_handles_korean_width(self):
        # 한글이 섞여도 예외 없이 정렬 문자열을 만들 수 있는지만 확인
        text = format_table(["카테고리"], [["food"], ["용돈"]])
        self.assertIn("food", text)
        self.assertIn("용돈", text)


if __name__ == "__main__":
    unittest.main()
