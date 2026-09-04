"""자잘한 헬퍼 함수 모음."""
from __future__ import annotations

import unicodedata


def parse_tags(raw: str | None) -> list[str]:
    """'meal,lunch' -> ['meal', 'lunch']. 빈 값이면 빈 리스트."""
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _display_width(text: str) -> int:
    """한글 등 넓은 글자는 폭 2로 계산해 표가 삐뚤어지지 않게 한다."""
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
    return width


def format_table(headers: list[str], rows: list[list]) -> str:
    """
    외부 라이브러리 없이 문자열 폭 계산만으로 표를 정렬해 문자열로 반환한다.
    (보너스 3번: 콘솔 출력 포맷 개선)
    """
    str_rows = [[str(cell) for cell in row] for row in rows]
    col_count = len(headers)
    widths = [_display_width(h) for h in headers]
    for row in str_rows:
        for i in range(col_count):
            widths[i] = max(widths[i], _display_width(row[i]))

    def pad(cell: str, width: int) -> str:
        return cell + " " * (width - _display_width(cell))

    lines = ["  ".join(pad(h, w) for h, w in zip(headers, widths))]
    lines.append("  ".join("-" * w for w in widths))
    for row in str_rows:
        lines.append("  ".join(pad(c, w) for c, w in zip(row, widths)))
    return "\n".join(lines)
