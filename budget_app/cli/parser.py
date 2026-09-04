"""argparse 서브커맨드 정의 + 커맨드 디스패치."""
from __future__ import annotations

import argparse
import sys

from . import handlers
from .context import build_context


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app", description="나만의 용돈 기입장")
    parser.add_argument("--datadir", default="./data", help="데이터 저장 폴더 (기본: ./data)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add", help="거래 추가 (대화형)")

    p_list = sub.add_parser("list", help="거래 목록 (최신순)")
    p_list.add_argument("--limit", type=int, default=20)

    p_search = sub.add_parser("search", help="조건 검색")
    p_search.add_argument("--from", dest="date_from")
    p_search.add_argument("--to", dest="date_to")
    p_search.add_argument("--category")
    p_search.add_argument("--type", choices=["income", "expense"])
    p_search.add_argument("--q", help="메모 키워드")
    p_search.add_argument("--tag")

    p_summary = sub.add_parser("summary", help="월별 요약")
    p_summary.add_argument("--month", required=True, help="YYYY-MM")
    p_summary.add_argument("--top", type=int, default=3)

    p_budget = sub.add_parser("budget", help="예산 설정/조회")
    budget_sub = p_budget.add_subparsers(dest="budget_command", required=True)
    p_budget_set = budget_sub.add_parser("set")
    p_budget_set.add_argument("--month", required=True)
    p_budget_set.add_argument("--amount", type=int, required=True)

    p_category = sub.add_parser("category", help="카테고리 관리")
    cat_sub = p_category.add_subparsers(dest="category_command", required=True)
    cat_sub.add_parser("list")
    p_cat_add = cat_sub.add_parser("add")
    p_cat_add.add_argument("name", nargs="?")  # 없으면 대화형 입력
    p_cat_remove = cat_sub.add_parser("remove")
    p_cat_remove.add_argument("name")

    p_update = sub.add_parser("update", help="거래 수정")
    p_update.add_argument("--id", required=True)
    p_update.add_argument("--date")
    p_update.add_argument("--type", choices=["income", "expense"])
    p_update.add_argument("--category")
    p_update.add_argument("--amount", type=int)
    p_update.add_argument("--memo")
    p_update.add_argument("--tags")

    p_delete = sub.add_parser("delete", help="거래 삭제")
    p_delete.add_argument("--id", required=True)

    p_import = sub.add_parser("import", help="CSV 가져오기")
    p_import.add_argument("--from", dest="csv_path", required=True)

    p_export = sub.add_parser("export", help="CSV 내보내기")
    p_export.add_argument("--out", required=True)
    p_export.add_argument("--month")
    p_export.add_argument("--from", dest="date_from")
    p_export.add_argument("--to", dest="date_to")

    sub.add_parser("backup", help="데이터 파일 백업 (보너스)")

    p_recurring = sub.add_parser("recurring", help="반복 거래 관리 (보너스)")
    recurring_sub = p_recurring.add_subparsers(dest="recurring_command", required=True)
    recurring_sub.add_parser("add", help="반복 거래 등록 (대화형)")
    recurring_sub.add_parser("list", help="반복 거래 목록")
    p_recurring_remove = recurring_sub.add_parser("remove")
    p_recurring_remove.add_argument("--id", required=True)
    p_recurring_generate = recurring_sub.add_parser("generate", help="해당 월 거래 생성")
    p_recurring_generate.add_argument("--month", required=True)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ctx = build_context(args.datadir)

    if args.command == "budget":
        if args.budget_command == "set":
            handlers.handle_budget_set(ctx, args)
        return 0

    if args.command == "category":
        if args.category_command == "list":
            handlers.handle_category_list(ctx, args)
        elif args.category_command == "add":
            handlers.handle_category_add(ctx, args)
        elif args.category_command == "remove":
            handlers.handle_category_remove(ctx, args)
        return 0

    if args.command == "recurring":
        if args.recurring_command == "add":
            handlers.handle_recurring_add(ctx, args)
        elif args.recurring_command == "list":
            handlers.handle_recurring_list(ctx, args)
        elif args.recurring_command == "remove":
            handlers.handle_recurring_remove(ctx, args)
        elif args.recurring_command == "generate":
            handlers.handle_recurring_generate(ctx, args)
        return 0

    dispatch = {
        "add": handlers.handle_add,
        "list": handlers.handle_list,
        "search": handlers.handle_search,
        "summary": handlers.handle_summary,
        "update": handlers.handle_update,
        "delete": handlers.handle_delete,
        "import": handlers.handle_import,
        "export": handlers.handle_export,
        "backup": handlers.handle_backup,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(ctx, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
