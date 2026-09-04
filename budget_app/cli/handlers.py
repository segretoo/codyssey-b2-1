"""각 서브커맨드의 실제 동작. argparse가 파싱한 args와 AppContext를 받아 실행한다."""
from __future__ import annotations

import shutil
from datetime import datetime

from ..decorators import handle_errors, log_execution, measure_time
from ..exceptions import ValidationError
from ..utils import format_table, parse_tags
from .context import AppContext


@handle_errors
@log_execution
def handle_add(ctx: AppContext, args) -> None:
    date = input("날짜(YYYY-MM-DD): ").strip()
    type_ = input("타입(income/expense): ").strip()

    # 애매했던 지점 보완: 미등록 카테고리면 바로 에러 종료가 아니라
    # 안내 후 재입력하거나 그 자리에서 등록하도록 유도한다.
    category = input("카테고리: ").strip()
    while not ctx.category_service.exists(category):
        print(f"[안내] 등록되지 않은 카테고리입니다: {category}")
        print(f"[안내] 등록된 카테고리: {', '.join(ctx.category_service.list_all())}")
        choice = input("새 카테고리로 등록하려면 y, 다시 입력하려면 Enter: ").strip().lower()
        if choice == "y":
            ctx.category_service.add(category)
            print(f"[저장 완료] category={category}")
            break
        category = input("카테고리: ").strip()

    amount_raw = input("금액(양수): ").strip()
    memo = input("메모(선택): ").strip()
    tags_raw = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    try:
        amount = int(amount_raw)
    except ValueError:
        raise ValidationError(f"금액은 숫자여야 합니다: {amount_raw}")

    tx = ctx.transaction_service.add(
        date=date,
        type_=type_,
        category=category,
        amount=amount,
        memo=memo,
        tags=parse_tags(tags_raw),
    )
    print(f"[저장 완료] id={tx.id}")


@handle_errors
@measure_time
def handle_list(ctx: AppContext, args) -> None:
    rows = ctx.transaction_service.list_recent(limit=args.limit)
    if not rows:
        print("데이터 없음")
        return
    headers = ["id", "날짜", "타입", "카테고리", "금액", "메모"]
    table = [[tx.id, tx.date, tx.type.value, tx.category, tx.amount, tx.memo] for tx in rows]
    print(format_table(headers, table))


@handle_errors
def handle_search(ctx: AppContext, args) -> None:
    rows = ctx.transaction_service.search(
        date_from=args.date_from,
        date_to=args.date_to,
        category=args.category,
        type_=args.type,
        query=args.q,
        tag=args.tag,
    )
    if not rows:
        print("데이터 없음")
        return
    headers = ["id", "날짜", "타입", "카테고리", "금액", "메모"]
    table = [[tx.id, tx.date, tx.type.value, tx.category, tx.amount, tx.memo] for tx in rows]
    print(format_table(headers, table))


@handle_errors
def handle_summary(ctx: AppContext, args) -> None:
    result = ctx.transaction_service.summary(month=args.month, top_n=args.top)
    if not result["found_any"]:
        print("데이터 없음")
        return

    print(f"총 수입: {result['total_income']}원")
    print(f"총 지출: {result['total_expense']}원")
    print(f"잔액: {result['balance']}원")

    evaluation = ctx.budget_service.evaluate(args.month, result["total_expense"])
    if evaluation:
        print(f"예산: {evaluation['budget']}원 (사용률 {evaluation['usage_rate']:.1f}%)")
        if evaluation["over"]:
            print("[경고] 예산을 초과했습니다.")

    if result["top_categories"]:
        print(f"지출 TOP {args.top}")
        for i, (category, amount) in enumerate(result["top_categories"], start=1):
            print(f"{i}) {category} {amount}원")


@handle_errors
def handle_budget_set(ctx: AppContext, args) -> None:
    ctx.budget_service.set_budget(args.month, args.amount)
    print(f"[저장 완료] {args.month} 예산 {args.amount}원")


@handle_errors
def handle_category_list(ctx: AppContext, args) -> None:
    names = ctx.category_service.list_all()
    if not names:
        print("데이터 없음")
        return
    print(format_table(["카테고리"], [[name] for name in names]))


@handle_errors
def handle_category_add(ctx: AppContext, args) -> None:
    name = args.name or input("카테고리명: ").strip()
    ctx.category_service.add(name)
    print(f"[저장 완료] category={name}")


@handle_errors
def handle_category_remove(ctx: AppContext, args) -> None:
    ctx.category_service.remove(args.name)
    print(f"[삭제 완료] category={args.name}")


@handle_errors
def handle_update(ctx: AppContext, args) -> None:
    tx = ctx.transaction_service.update(
        args.id,
        date=args.date,
        type=args.type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=args.tags,
    )
    print(f"[수정 완료] id={tx.id}")


@handle_errors
def handle_delete(ctx: AppContext, args) -> None:
    ctx.transaction_service.delete(args.id)
    print(f"[삭제 완료] id={args.id}")


@handle_errors
def handle_import(ctx: AppContext, args) -> None:
    imported, skipped = ctx.transaction_service.import_csv(args.csv_path)
    print(f"[완료] imported={imported}, skipped={skipped}")


@handle_errors
def handle_export(ctx: AppContext, args) -> None:
    if not args.month and not (args.date_from and args.date_to):
        raise ValidationError("export는 --month 또는 --from/--to 조건이 필요합니다")
    count = ctx.transaction_service.export_csv(
        args.out, month=args.month, date_from=args.date_from, date_to=args.date_to
    )
    print(f"[완료] {args.out} ({count} records)")


# ---- 보너스 1: 백업 기능 ----

@handle_errors
def handle_backup(ctx: AppContext, args) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ctx.datadir / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    source_files = ["transactions.jsonl", "categories.jsonl", "budgets.jsonl", "recurring.jsonl"]
    copied = []
    for name in source_files:
        src = ctx.datadir / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
            copied.append(name)

    print(f"[백업 완료] {backup_dir} ({len(copied)}개 파일)")


# ---- 보너스 2: 반복 내역 기능 ----

@handle_errors
def handle_recurring_add(ctx: AppContext, args) -> None:
    type_ = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount_raw = input("금액(양수): ").strip()
    day_raw = input("매월 반복일(1~28): ").strip()
    memo = input("메모(선택): ").strip()
    tags_raw = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    try:
        amount = int(amount_raw)
    except ValueError:
        raise ValidationError(f"금액은 숫자여야 합니다: {amount_raw}")
    try:
        day_of_month = int(day_raw)
    except ValueError:
        raise ValidationError(f"반복일은 숫자여야 합니다: {day_raw}")

    rule = ctx.recurring_service.add(
        day_of_month=day_of_month,
        type_=type_,
        category=category,
        amount=amount,
        memo=memo,
        tags=parse_tags(tags_raw),
    )
    print(f"[저장 완료] id={rule.id}")


@handle_errors
def handle_recurring_list(ctx: AppContext, args) -> None:
    rules = ctx.recurring_service.list_all()
    if not rules:
        print("데이터 없음")
        return
    headers = ["id", "매월", "타입", "카테고리", "금액", "메모"]
    table = [
        [r.id, f"{r.day_of_month}일", r.type.value, r.category, r.amount, r.memo] for r in rules
    ]
    print(format_table(headers, table))


@handle_errors
def handle_recurring_remove(ctx: AppContext, args) -> None:
    ctx.recurring_service.remove(args.id)
    print(f"[삭제 완료] id={args.id}")


@handle_errors
def handle_recurring_generate(ctx: AppContext, args) -> None:
    created, skipped = ctx.recurring_service.generate_for_month(args.month)
    print(f"[완료] 생성 {created}건, 이미 생성되어 건너뜀 {skipped}건")
