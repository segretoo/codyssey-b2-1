"""
TransactionRepository: transactions.jsonl 파일의 CRUD 전담.

- stream_all(): 파일을 한 줄씩 읽어 Transaction으로 변환해 yield하는 제너레이터.
  list/search/summary 등 조회 계열은 전부 이걸 순회하며 처리하고, 절대
  list()로 통째로 모아서 쓰지 않는다.
- update()/delete(): 임시 파일에 전체를 다시 쓰고 os.replace()로 원자적
  교체하는 패턴을 쓴다. 쓰는 도중 프로그램이 죽어도 원본 파일이 깨지지 않는다.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional

from ..exceptions import NotFoundError
from ..models import Transaction


class TransactionRepository:
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.touch(exist_ok=True)

    def stream_all(self) -> Iterator[Transaction]:
        """파일을 한 줄씩 읽어 Transaction으로 변환해 yield한다."""
        with self.filepath.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Transaction.from_dict(json.loads(line))

    def append(self, tx: Transaction) -> None:
        """새 거래 1건을 파일 끝에 JSONL 한 줄로 추가한다."""
        with self.filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")

    def find_by_id(self, tx_id: str) -> Optional[Transaction]:
        """stream_all()을 순회하며 id가 일치하는 첫 건을 반환, 없으면 None."""
        for tx in self.stream_all():
            if tx.id == tx_id:
                return tx
        return None

    def next_id(self) -> str:
        """기존 id 중 가장 큰 번호 다음 값을 'TX-000001' 형태로 반환한다."""
        max_num = 0
        for tx in self.stream_all():
            try:
                num = int(tx.id.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
        return f"TX-{max_num + 1:06d}"

    def update(self, tx_id: str, updater: Callable[[Transaction], Transaction]) -> Transaction:
        """
        tx_id와 일치하는 항목을 updater(tx)로 교체하고 전체를 원자적으로 재작성한다.
        일치하는 id가 없으면 NotFoundError.
        """
        updated_tx: Optional[Transaction] = None
        kept: list[Transaction] = []
        for tx in self.stream_all():
            if tx.id == tx_id:
                updated_tx = updater(tx)
                kept.append(updated_tx)
            else:
                kept.append(tx)

        if updated_tx is None:
            raise NotFoundError(f"존재하지 않는 거래 id입니다: {tx_id}")

        self._rewrite_all(kept)
        return updated_tx

    def delete(self, tx_id: str) -> None:
        """tx_id와 일치하는 항목만 제외하고 전체를 원자적으로 재작성한다."""
        found = False
        kept: list[Transaction] = []
        for tx in self.stream_all():
            if tx.id == tx_id:
                found = True
                continue
            kept.append(tx)

        if not found:
            raise NotFoundError(f"존재하지 않는 거래 id입니다: {tx_id}")

        self._rewrite_all(kept)

    def is_category_in_use(self, category: str) -> bool:
        """제너레이터를 순회하다 첫 매칭에서 바로 True를 반환 (전체를 다 안 봄)."""
        for tx in self.stream_all():
            if tx.category == category:
                return True
        return False

    def _rewrite_all(self, transactions: Iterable[Transaction]) -> None:
        dir_ = self.filepath.parent
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                for tx in transactions:
                    tmp_f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")
            os.replace(tmp_path, self.filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
