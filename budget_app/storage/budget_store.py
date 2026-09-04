"""BudgetStore: budgets.jsonl 파일 담당. 월(month)별 예산 금액 1개씩 저장."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


class BudgetStore:
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.touch(exist_ok=True)

    def _read_all(self) -> dict[str, int]:
        budgets: dict[str, int] = {}
        with self.filepath.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    budgets[rec["month"]] = rec["amount"]
        return budgets

    def get(self, month: str) -> int | None:
        return self._read_all().get(month)

    def set(self, month: str, amount: int) -> None:
        budgets = self._read_all()
        budgets[month] = amount
        self._rewrite(budgets)

    def _rewrite(self, budgets: dict[str, int]) -> None:
        dir_ = self.filepath.parent
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                for month, amount in budgets.items():
                    tmp_f.write(json.dumps({"month": month, "amount": amount}, ensure_ascii=False) + "\n")
            os.replace(tmp_path, self.filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
