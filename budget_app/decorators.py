"""
공통 관심사(로그, 실행 시간 측정, 예외 처리)를 분리하는 데코레이터 모음.
CLI 커맨드 핸들러 최상단에 적용해서 쓴다.
"""
from __future__ import annotations

import functools
import logging
import sys
import time

from .exceptions import BudgetAppError

logger = logging.getLogger("budget_app")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def log_execution(func):
    """함수 호출 시작/종료를 로그로 남긴다."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"실행 시작: {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"실행 종료: {func.__name__}")
        return result
    return wrapper


def measure_time(func):
    """함수 실행 시간을 측정해 로그로 남긴다."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} 실행 시간: {elapsed:.4f}s")
        return result
    return wrapper


def handle_errors(func):
    """
    BudgetAppError 계열 예외를 '원인 + 힌트' 형태로만 출력하고
    (스택트레이스 노출 금지) exit code를 0이 아닌 값으로 종료한다.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BudgetAppError as e:
            print(f"[오류] {e}")
            print("[힌트] 입력 값을 다시 확인해주세요.")
            sys.exit(1)
        except Exception as e:  # 예상 못한 오류도 스택트레이스 없이 처리
            print(f"[오류] 예상치 못한 문제가 발생했습니다: {e}")
            sys.exit(1)
    return wrapper
