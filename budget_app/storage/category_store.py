"""
CategoryStore: categories.jsonl 파일 담당.

카테고리 파일이 비어있으면(=최초 실행) 기본 카테고리를 자동 생성한다.
(스펙 3번 '안 A' 선택 — add가 처음부터 막히지 않도록)
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from ..exceptions import NotFoundError, ValidationError

DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary", "etc"]


class CategoryStore:
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.touch(exist_ok=True)
        if self.filepath.stat().st_size == 0:
            self._init_defaults()

    def _init_defaults(self) -> None:
        with self.filepath.open("w", encoding="utf-8") as f:
            for name in DEFAULT_CATEGORIES:
                f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")

    def list_all(self) -> list[str]:
        names: list[str] = []
        with self.filepath.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    names.append(json.loads(line)["name"])
        return names

    def exists(self, name: str) -> bool:
        return name in self.list_all()

    def add(self, name: str) -> None:
        if not name:
            raise ValidationError("카테고리명은 비어있을 수 없습니다")
        if self.exists(name):
            raise ValidationError(f"이미 존재하는 카테고리입니다: {name}")
        with self.filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")

    def remove(self, name: str) -> None:
        names = self.list_all()
        if name not in names:
            raise NotFoundError(f"존재하지 않는 카테고리입니다: {name}")
        self._rewrite([n for n in names if n != name])

    def _rewrite(self, names: list[str]) -> None:
        dir_ = self.filepath.parent
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                for name in names:
                    tmp_f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")
            os.replace(tmp_path, self.filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
