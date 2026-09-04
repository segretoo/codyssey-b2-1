"""RecurringStore: recurring.jsonl 파일 담당. 반복 거래 규칙 CRUD (보너스 2번)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterable, Iterator

from ..exceptions import NotFoundError
from ..models import RecurringRule


class RecurringStore:
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.touch(exist_ok=True)

    def stream_all(self) -> Iterator[RecurringRule]:
        with self.filepath.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield RecurringRule.from_dict(json.loads(line))

    def append(self, rule: RecurringRule) -> None:
        with self.filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rule.to_dict(), ensure_ascii=False) + "\n")

    def next_id(self) -> str:
        max_num = 0
        for rule in self.stream_all():
            try:
                num = int(rule.id.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
        return f"RC-{max_num + 1:06d}"

    def delete(self, rule_id: str) -> None:
        found = False
        kept: list[RecurringRule] = []
        for rule in self.stream_all():
            if rule.id == rule_id:
                found = True
                continue
            kept.append(rule)
        if not found:
            raise NotFoundError(f"존재하지 않는 반복 규칙 id입니다: {rule_id}")
        self._rewrite_all(kept)

    def _rewrite_all(self, rules: Iterable[RecurringRule]) -> None:
        dir_ = self.filepath.parent
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                for rule in rules:
                    tmp_f.write(json.dumps(rule.to_dict(), ensure_ascii=False) + "\n")
            os.replace(tmp_path, self.filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
