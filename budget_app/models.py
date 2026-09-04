"""
데이터 모델 계층.

- Transaction: 거래 1건을 표현하는 순수 데이터 클래스 (행위 없음)
- RecurringRule: 월급/월세처럼 매월 반복되는 거래의 "규칙"을 표현하는 데이터 클래스
- validate_*: 입력 검증 함수. 타입 힌트는 강제력이 없으므로
  여기서 직접 조건을 확인하고 실패하면 ValidationError를 던진다.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum

from .exceptions import ValidationError


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class Transaction:
    id: str
    date: str  # "YYYY-MM-DD" 문자열로 저장 (JSONL 직렬화 단순화 목적)
    type: TransactionType
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=data["id"],
            date=data["date"],
            type=TransactionType(data["type"]),
            category=data["category"],
            amount=int(data["amount"]),
            memo=data.get("memo", "") or "",
            tags=data.get("tags") or [],
        )


@dataclass
class RecurringRule:
    """월급/월세처럼 매월 반복되는 거래 규칙 (보너스 2번: 반복 내역 기능)."""
    id: str
    day_of_month: int  # 1~28: 매월 이 날짜에 거래를 생성
    type: TransactionType
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringRule":
        return cls(
            id=data["id"],
            day_of_month=int(data["day_of_month"]),
            type=TransactionType(data["type"]),
            category=data["category"],
            amount=int(data["amount"]),
            memo=data.get("memo", "") or "",
            tags=data.get("tags") or [],
        )


def validate_date(value: str) -> None:
    """YYYY-MM-DD 형식인지 검증한다."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise ValidationError(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD): {value}") from e


def validate_month(value: str) -> None:
    """YYYY-MM 형식인지 검증한다."""
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as e:
        raise ValidationError(f"월 형식이 올바르지 않습니다 (YYYY-MM): {value}") from e


def validate_amount(value: int) -> None:
    """금액은 양수여야 한다."""
    if value <= 0:
        raise ValidationError(f"금액은 양수여야 합니다: {value}")


def validate_type(value: str) -> TransactionType:
    """type은 income/expense 중 하나여야 한다."""
    try:
        return TransactionType(value)
    except ValueError as e:
        raise ValidationError(f"type은 income 또는 expense여야 합니다: {value}") from e


def validate_day_of_month(value: int) -> None:
    """
    반복 거래의 매월 반복일은 1~28로 제한한다.
    (29~31일은 없는 달이 있어 매월 생성 시 예외가 생기므로 범위를 좁혀 단순화)
    """
    if not (1 <= value <= 28):
        raise ValidationError(f"매월 반복일은 1~28 사이여야 합니다: {value}")
