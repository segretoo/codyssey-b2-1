# 나만의 용돈 기입장 (budget_app)

Python 표준 라이브러리만으로 구현한 CLI 가계부 프로그램입니다.

## 실행 방법

Python 3.10 이상이 필요합니다 (외부 라이브러리 설치 불필요).

```bash
python -m budget_app <command> [options]

python -m budget_app add
python -m budget_app --datadir ./data list --limit 10
python -m budget_app --help
```

모든 명령은 `--help` 로 사용법을 확인할 수 있습니다. (예: `python -m budget_app add --help`)

## 설계 결정 (스펙에서 선택지로 남겨둔 항목)

| 항목 | 선택 | 이유 |
|---|---|---|
| 저장 포맷 | **JSONL** | 한 줄 = 한 레코드라 append/스트리밍 read가 단순하고, tags 같은 리스트 필드를 다루기 쉬움 |
| update 방식 | **옵션 기반** (`update --id <id> [--field ...]`) | 재현 가능하고 스크립트/자동 테스트로 검증하기 쉬움 |
| 카테고리 초기 상태 | **안 A**: 카테고리 파일이 비어있으면 기본 카테고리(`food, transport, rent, salary, etc`)를 자동 생성 | add가 처음부터 막히지 않아 초기 사용성이 좋음 |
| 카테고리 삭제(사용 중일 때) | **차단** (대체 카테고리 요구 대신 삭제 자체를 막음) | 데이터 유실 없이 가장 단순하고 안전한 정책 |

## 저장 파일 위치 / 형식

기본 저장 폴더는 `./data` 이며, `--datadir` 옵션으로 변경할 수 있습니다.

```
data/
├── transactions.jsonl   # 거래 내역 (한 줄 = 거래 1건)
├── categories.jsonl     # 카테고리 목록 (한 줄 = 카테고리 1개)
├── budgets.jsonl         # 월별 예산 (한 줄 = 1개월치 예산)
├── recurring.jsonl       # 반복 거래 규칙 (한 줄 = 규칙 1개, 보너스)
└── backups/               # backup 명령으로 생성되는 타임스탬프별 백업 (보너스)
```

`transactions.jsonl` 한 줄 예시:

```json
{"id": "TX-000001", "date": "2024-01-15", "type": "expense", "category": "food", "amount": 18000, "memo": "점심", "tags": ["meal"]}
```

## 주요 명령 예시

```bash
# 거래 추가 (대화형). 미등록 카테고리를 입력하면 그 자리에서
# 등록하거나(y) 다시 입력하도록 안내한다.
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000001

# 목록 조회 (최신순, 표 형태로 정렬 출력)
$ python -m budget_app list --limit 3

# 조건 검색
$ python -m budget_app search --category food --from 2024-01-01 --to 2024-01-31

# 월별 요약 + 예산 사용률
$ python -m budget_app budget set --month 2024-01 --amount 500000
$ python -m budget_app summary --month 2024-01 --top 3

# 카테고리 관리
$ python -m budget_app category add
$ python -m budget_app category list
$ python -m budget_app category remove food   # 사용 중이면 거부됨

# 거래 수정/삭제
$ python -m budget_app update --id TX-000001 --amount 18000 --memo "점심(수정)"
$ python -m budget_app delete --id TX-000001

# CSV 내보내기/가져오기
$ python -m budget_app export --out export.csv --month 2024-01
$ python -m budget_app import --from import.csv

# 데이터 백업 (보너스)
$ python -m budget_app backup

# 반복 거래: 월급/월세 등록 후 특정 월에 일괄 생성 (보너스)
$ python -m budget_app recurring add
$ python -m budget_app recurring list
$ python -m budget_app recurring generate --month 2024-03
$ python -m budget_app recurring remove --id RC-000001
```

## import / export CSV 스키마

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

공통: UTF-8, 헤더 포함. `export`는 `--month` 또는 `--from`/`--to` 중 하나 이상의 조건이 필수입니다. `import` 시 행 단위로 검증하며, 검증에 실패한 행은 건너뛰고(skip) 마지막에 `imported/skipped` 건수를 출력합니다.

## 아키텍처

```
budget_app/
├── models.py           # Transaction, RecurringRule dataclass + 검증 함수
├── exceptions.py       # 커스텀 예외 계층
├── decorators.py         # log_execution / measure_time / handle_errors
├── utils.py               # 태그 파싱, 콘솔 테이블 포맷터
├── storage/               # 파일 I/O 전담 (제너레이터 스트리밍 read, 임시파일+os.replace 원자적 write)
├── services/               # 비즈니스 로직 (검증, 집계, 참조 무결성, 반복거래 생성)
└── cli/                     # argparse 서브커맨드 + 커맨드 핸들러
```

- **제너레이터 스트리밍**: `TransactionRepository.stream_all()`이 파일을 한 줄씩 읽어 `yield`. `search`/`summary`는 이 제너레이터를 그대로 순회하며 조건에 맞는 것만 골라내거나 집계값만 유지하므로, 전체 레코드 수와 무관하게 메모리 사용량이 작다. `list`(최신 N건)는 정렬이 필요해 전체를 봐야 하지만, `list()+sort()`로 전부 메모리에 모으는 대신 `heapq.nlargest(limit, ...)`를 사용해 **메모리 사용량을 limit 크기로 제한**했다 (시간복잡도는 전체를 한 번 훑는 건 동일하지만, 메모리에는 최대 limit개만 남는다).
- **원자적 쓰기**: `update`/`delete`는 임시 파일에 전체를 다시 쓰고 `os.replace()`로 교체한다. 쓰는 도중 프로세스가 죽어도 원본 파일이 깨지지 않는다.
- **데코레이터**: `@handle_errors`가 모든 커맨드 핸들러 최상단에서 예외를 잡아 "원인 + 힌트" 형태로만 출력하고 exit code 1로 종료한다 (스택트레이스 노출 없음). `@log_execution`, `@measure_time`은 각각 실행 로그/시간 측정을 분리한다.
- **타입 힌트**: 모든 함수의 매개변수/반환값에 타입을 명시해 모듈 간 계약을 명확히 했다. 단, 타입 힌트는 런타임을 강제하지 않으므로 `models.py`의 `validate_*` 함수로 실제 검증을 별도로 수행한다.
- **add의 카테고리 재입력 유도**: `add` 실행 중 미등록 카테고리를 입력하면 즉시 에러로 종료하지 않고, 등록된 카테고리 목록을 보여준 뒤 그 자리에서 새 카테고리로 등록하거나(`y`) 다시 입력하도록 안내한다.

## 종료 코드

정상 종료는 `0`, 검증 실패/데이터 없음 등 오류 상황은 `0`이 아닌 값(`1`)으로 종료합니다. 필수 옵션이 누락된 경우 argparse 자체가 사용법을 출력하고 exit code `2`로 종료합니다 (스택트레이스 없음).

## 개발 환경 / 제약

- Python 3.10 이상, 표준 라이브러리만 사용 (외부 라이브러리 설치 불필요 — json/os/tempfile/pathlib/typing/dataclasses/datetime/enum/functools/logging/sys/time/csv/argparse/heapq/shutil/unicodedata)
- 저장 파일 3개 이상(transactions/categories/budgets, 보너스로 recurring 추가)으로 분리

## 보너스 구현 현황

| 보너스 | 상태 | 비고 |
|---|---|---|
| 1. 백업 기능 | ✅ | `backup` — `data/backups/<타임스탬프>/`에 4개 파일 복사 |
| 2. 반복 내역 기능 | ✅ | `recurring add/list/remove/generate` — 태그 기반 중복 생성 방지 |
| 3. 콘솔 출력 테이블 정렬 | ✅ | `utils.format_table` — 외부 라이브러리 없이 문자열 폭 계산으로 정렬 (한글은 폭 2로 계산) |
| 4. 저장 원자성 강화 | ✅ | update/delete/category remove/budget set 전부 임시파일+`os.replace()` 패턴 |

## 테스트

```bash
python -m unittest discover -s tests -v
```

24개 테스트(기본 CRUD, 검증, 참조무결성, 반복거래 생성/중복방지, 테이블 포맷 등)로 서비스 계층을 검증합니다.

## 실행 예시 검증

`add`(재입력/등록 유도 포함) → `list`(테이블 포맷) → `search` → `budget set` → `summary` → `update` → `delete` → `export`/`import` → `backup` → `recurring add/list/generate/remove` 순서로 수동 테스트를 완료했습니다. 200건 이상 데이터에서도 `list`/`summary`가 정상 동작함을 확인했습니다.
