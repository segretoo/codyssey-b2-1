<div align="center">

# 💰 나만의 용돈 기입장 (budget_app)

### Python 표준 라이브러리만으로 만든 CLI 가계부 · 제너레이터 스트리밍과 원자적 파일 쓰기로 안전성 확보

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Storage](https://img.shields.io/badge/storage-JSONL-lightgrey)

</div>

> 기능이 도는 것보다, 예외 상황에서도 데이터가 안전하고 코드가 유지보수 가능한 구조를 갖추는 것을 목표로 만들었습니다.

**미션**: B2-1 · 나만의 용돈 기입장 프로그램 만들기

## 프로젝트 개요

수입과 지출을 파일에 영구 저장하고, 검색·월별 요약·예산 관리까지 지원하는 CLI 가계부입니다. 표면적인 목표는 "가계부 기능 완성"이지만, 실제로 이 프로젝트에서 집중한 건 다음 다섯 가지입니다: 파일 기반 영속 저장, 제너레이터를 이용한 메모리 효율적 스트리밍 처리, 데코레이터를 통한 공통 관심사 분리, 타입 힌트를 통한 모듈 간 계약 명시, 그리고 책임에 따른 모듈화입니다.

그래서 코드는 `models`(데이터 구조) → `storage`(파일 I/O) → `services`(비즈니스 로직) → `cli`(사용자 인터페이스) 4계층으로 나눴고, 각 계층이 서로의 내부 구현을 몰라도 되도록 경계를 명확히 그었습니다. 저장 형식은 JSONL, update/delete는 임시파일 + 원자적 교체 패턴을 사용했으며, 반복거래·백업·콘솔 테이블 정렬 등 보너스 과제도 함께 구현했습니다.

## 주요 기능

| 명령                                 | 설명                                                                |
| ------------------------------------ | ------------------------------------------------------------------- |
| `add`                                | 거래 추가 (대화형, 미등록 카테고리 재입력/즉석등록 유도)            |
| `list --limit N`                     | 최근 거래 N건 조회 (최신순)                                         |
| `search`                             | `--category`/`--type`/`--from`/`--to`/`--q`/`--tag` 조건 검색       |
| `summary --month`                    | 월별 수입/지출/잔액 + 예산 사용률/초과 경고 + 카테고리별 지출 TOP N |
| `budget set`                         | 월별 예산 설정                                                      |
| `category add/list/remove`           | 카테고리 관리 (사용 중이면 삭제 차단)                               |
| `update` / `delete`                  | 거래 수정/삭제 (`--id` 지정)                                        |
| `export` / `import`                  | CSV 내보내기/가져오기                                               |
| `backup`                             | 데이터 파일 타임스탬프 백업                                         |
| `recurring add/list/remove/generate` | 월급/월세 등 반복 거래 등록 및 특정 월 일괄 생성                    |

## 개발 환경

- 언어/런타임: Python 3.10 이상 (3.12, 3.14에서 동작 확인)
- 주요 도구: VS Code, Git/GitHub, `unittest`(테스트), `mypy`(타입 검증 — 개발 시에만 사용, 실행에는 불필요)
- 외부 라이브러리: 없음. 표준 라이브러리만 사용 (`json`, `os`, `tempfile`, `pathlib`, `typing`, `dataclasses`, `datetime`, `enum`, `functools`, `logging`, `sys`, `time`, `csv`, `argparse`, `heapq`, `shutil`, `unicodedata`)
- 실행 방식: 로컬 실행 (`python -m budget_app`)
- 권장 환경: Windows(Git Bash) / macOS 둘 다 동작 확인

## 배포 & 실행 방법

- GitHub 저장소: https://github.com/segretoo/CodysseyB2-1

```bash
python -m budget_app --help
python -m budget_app add
python -m unittest discover -s tests -v   # 테스트 24개 실행
```

## 프로젝트 구조

```
budget_app/
├── models.py                        # Transaction, RecurringRule + 검증 함수
├── exceptions.py                     # 커스텀 예외 계층
├── decorators.py                       # log_execution / measure_time / handle_errors
├── utils.py                             # 태그 파싱, 콘솔 테이블 포맷터
├── storage/                              # 파일 I/O 전담
│   ├── transaction_repository.py
│   ├── category_store.py
│   ├── budget_store.py
│   └── recurring_store.py
├── services/                               # 비즈니스 로직
│   ├── transaction_service.py
│   ├── category_service.py
│   ├── budget_service.py
│   └── recurring_service.py
└── cli/                                       # 입출력 계층
    ├── context.py                              # storage/service 조립
    ├── handlers.py                              # 각 명령의 실제 동작
    └── parser.py                                # argparse 서브커맨드 정의
tests/
└── test_budget_app.py                # 서비스 계층 unittest 24개
```

`cli/context.py`가 모든 storage/service 객체를 조립하는 지점이고, `cli/handlers.py`는 그 객체들만 호출할 뿐 파일이 어떻게 저장되는지는 모릅니다.

## CLI 사용법 상세

```bash
# 거래
python -m budget_app add
python -m budget_app list --limit 10
python -m budget_app search --category food --from 2024-01-01 --to 2024-01-31
python -m budget_app update --id TX-000001 --amount 18000 --memo "수정"
python -m budget_app delete --id TX-000001

# 요약 / 예산
python -m budget_app summary --month 2024-01 --top 3
python -m budget_app budget set --month 2024-01 --amount 500000

# 카테고리
python -m budget_app category list
python -m budget_app category add
python -m budget_app category remove food

# 데이터 이동 / 백업
python -m budget_app export --out out.csv --month 2024-01
python -m budget_app import --from out.csv
python -m budget_app backup

# 반복 거래 (보너스)
python -m budget_app recurring add
python -m budget_app recurring generate --month 2024-03

# 저장 위치 변경 (모든 명령 공통)
python -m budget_app --datadir ./other_data list
```

## 데이터 모델 / 클래스 책임

`Transaction`(id, date, type, category, amount, memo, tags)과 `RecurringRule`(반복 규칙)을 `dataclass`로 정의했습니다. dataclass를 쓴 이유는 "행위 없이 데이터만 담는 상자"라는 의도를 코드로 명확히 드러내기 위해서입니다 — 이 클래스들은 `to_dict()`/`from_dict()` 외에는 아무 로직도 갖지 않습니다.

클래스 책임 경계는 "이 클래스가 사라지면 어떤 지식이 함께 사라지는가"로 나눴습니다.

| 클래스                  | 갖고 있는 지식                                      |
| ----------------------- | --------------------------------------------------- |
| `TransactionRepository` | 파일이 어디 있고 어떤 형식(JSONL)인지               |
| `TransactionService`    | 어떤 입력이 유효한지, 어떤 카테고리 삭제가 위험한지 |
| `CategoryService`       | 카테고리 삭제 시 참조 무결성을 지켜야 한다는 규칙   |
| `AppContext`            | 위 객체들을 어떤 조합으로 묶어야 하는지             |

## 모듈 책임과 계층 분리

```
cli  →  services  →  storage  →  models
(입출력)   (규칙 판단)   (파일 처리)   (데이터 구조)
```

의존 방향은 항상 왼쪽에서 오른쪽으로만 흐릅니다. `storage`는 `services`가 뭘 하는지 몰라도 되고, `models`는 자신이 어떻게 저장되는지 전혀 모릅니다. 이 경계 덕분에 저장 형식을 JSONL에서 CSV로 바꾸는 상상을 해봐도 `storage/` 파일들만 고치면 되고 `services`/`cli`는 건드릴 필요가 없습니다.

## 저장 구조 상세

기본 저장 폴더는 `./data`이며 `--datadir`로 변경할 수 있습니다.

```
data/
├── transactions.jsonl   # 거래 내역
├── categories.jsonl     # 카테고리 목록
├── budgets.jsonl         # 월별 예산
├── recurring.jsonl        # 반복 거래 규칙
└── backups/                 # backup 명령 결과물
```

id는 `TX-000001`, `RC-000001`처럼 6자리 zero-padding을 사용합니다. 숫자만 늘어놓는 대신 접두어(`TX`/`RC`)를 붙인 이유는 로그나 CSV를 볼 때 어떤 종류의 레코드인지 한눈에 구분하기 위해서고, zero-padding은 문자열로 봐도 자릿수가 맞아 정렬이 어긋나지 않게 하기 위해서입니다.

`transactions.jsonl` 한 줄 예시:

```json
{
    "id": "TX-000001",
    "date": "2024-01-15",
    "type": "expense",
    "category": "food",
    "amount": 18000,
    "memo": "점심",
    "tags": ["meal"]
}
```

## 원자적 갱신 (Atomic Replace)

파일 중간의 특정 줄만 직접 덮어쓰면, 새 값의 길이가 원래 값과 다를 때 뒤 내용이 밀리며 파일이 깨집니다. 그래서 `update`/`delete`/`category remove`/`budget set` 전부 아래 패턴을 씁니다.

```python
fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
    for record in records:
        tmp_f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
os.replace(tmp_path, self.filepath)
```

`os.replace()`는 OS 수준에서 원자적이라, 쓰는 도중 프로세스가 죽어도 원본 파일은 "이전 상태 그대로" 또는 "새 상태 그대로" 둘 중 하나로만 남고, 절반만 써진 중간 상태로 깨지지 않습니다.

## 오류 처리와 예외 경계

```
BudgetAppError (기본)
├── ValidationError    (날짜/금액/타입/카테고리 검증 실패)
├── NotFoundError       (존재하지 않는 id/카테고리)
└── CategoryInUseError   (사용 중인 카테고리 삭제 시도)
```

`services/`는 문제가 생기면 위 예외를 그냥 던지기만 하고, "사용자에게 뭐라고 보여줄지"는 전혀 신경 쓰지 않습니다. 이걸 잡아서 화면에 출력하는 건 오직 `decorators.py`의 `handle_errors` 한 곳뿐입니다 — 즉 "내부 로직이 뭘 실패로 판단하는가"와 "실패를 사용자에게 어떻게 보여주는가"라는 두 가지 책임이 코드 상에서도 분리돼 있습니다.

```python
except BudgetAppError as e:
    print(f"[오류] {e}")
    print("[힌트] 입력 값을 다시 확인해주세요.")
    sys.exit(1)
```

## 학습 목표 & 설명

**Q. 코드를 3개 이상 모듈로 나누고, 각 모듈의 책임을 어떻게 나눴나요?**
**"데이터가 어떤 흐름을 타는가"를 기준으로 models → storage → services → cli 4계층으로 나눴습니다.**

- `models`는 데이터 구조만 정의하고 아무 동작도 하지 않습니다.
- `storage`는 파일을 실제로 읽고 쓰는 책임만 지고, 어떤 값이 유효한지는 모릅니다.
- `services`는 검증·집계·참조무결성 같은 규칙을 판단하고, 파일이 JSONL인지 CSV인지는 모릅니다.
- `cli`는 사용자 입력을 받아 `services`를 호출하고 결과를 출력할 뿐, 규칙 자체는 갖고 있지 않습니다.

**Q. 최소 2개 이상 클래스의 책임 경계를 어떻게 정했나요?**
**"이 클래스가 사라지면 어떤 지식이 함께 사라지는가"를 기준으로 나눴습니다.**

- `TransactionRepository`가 사라지면 "파일이 어디 있고 어떤 형식인지"에 대한 지식이 사라집니다. `TransactionService`는 이 지식이 없어도 동작합니다.
- `TransactionService`가 사라지면 "음수 금액은 안 된다", "미등록 카테고리는 안 된다" 같은 규칙이 사라집니다. `cli` 핸들러는 이 규칙을 몰라도 됩니다.
- `CategoryService`가 삭제 전에 `TransactionService.is_category_in_use()`를 호출하는 것도, "참조 무결성 판단"이라는 책임을 한 곳(서비스 계층)에만 모아두기 위해서입니다.

**Q. 파일 기반 update/delete를 어떻게 안전하게 처리했나요?**
**임시 파일에 전체를 새로 쓰고 `os.replace()`로 원자적으로 교체하는 패턴을 썼습니다.**

- 원본 파일 중간을 직접 덮어쓰면(seek 후 write) 새 값 길이가 다를 때 파일이 깨질 수 있습니다.
- 그래서 "전체를 임시 파일에 다 쓴 뒤, 다 쓰고 나서야 원자적으로 이름을 바꿔치기"하는 방식을 택했습니다.
- `os.replace()`는 OS 수준 원자적 연산이라, 쓰다가 프로세스가 죽어도 파일이 반쯤 써진 상태로 남지 않습니다.
- 구현 위치는 `storage/*.py`의 `_rewrite_all()`/`_rewrite()`이며, 자세한 코드는 위 "원자적 갱신" 섹션에 있습니다.

**Q. list/search를 제너레이터로 어떻게 구현했고, 왜 유리한가요?**
**`stream_all()`이 파일을 한 줄씩 읽어 `yield`하고, `search`는 조건에 맞는 것만, `list`는 `heapq`로 상위 N개만 메모리에 남깁니다.**

- 파일을 `read()`로 통째로 읽거나 리스트로 다 모으지 않고, `for line in f:`로 한 줄씩 읽습니다.
- `search`는 조건에 안 맞는 레코드를 그 자리에서 버리므로, 메모리엔 "매칭된 결과"만 남습니다.
- `summary`는 개별 레코드를 하나도 저장하지 않고 합계(딕셔너리)만 갱신합니다 — 메모리가 전체 건수가 아니라 카테고리 개수에만 비례하는, 스트리밍의 가장 확실한 이득을 보여주는 부분입니다.
- `list`는 원래 `list(stream_all())` + `sort()`로 전체를 모았는데, `heapq.nlargest(limit, stream_all())`로 바꿔 메모리 사용량을 limit 크기로 제한했습니다 (시간복잡도는 동일하게 전체를 한 번 훑지만, 메모리는 확실히 줄었습니다 — 아래 "설계 Trade-off"에 이 트레이드오프를 더 다룹니다).

**Q. 데코레이터로 어떤 공통 기능을 분리했고, 왜 필요했나요?**
**로그(`log_execution`), 실행시간 측정(`measure_time`), 예외처리(`handle_errors`) 3개를 분리했습니다.**

- 이 3개를 핵심 로직(예: 거래 추가) 안에 매번 넣으면, 커맨드가 10개면 똑같은 코드가 10번 반복됩니다.
- `@handle_errors` 하나만 각 핸들러 위에 붙이면, "문제가 생기면 스택트레이스 대신 원인+힌트를 출력하고 exit code 1로 종료한다"는 규칙이 모든 명령에 일관되게 적용됩니다.
- 핵심 로직(무엇을 하는가)과 부가 기능(실패를 어떻게 처리하는가)이 코드 상에서도 시각적으로 분리됩니다 — 데코레이터 줄만 봐도 이 함수에 어떤 공통 기능이 붙어있는지 바로 보입니다.

**Q. 타입 힌트로 얻는 이점을 실제 코드로 어떻게 확인했나요?**
**`cli/context.py`에서 `category_service`와 `budget_service` 자리를 일부러 바꿔치기한 뒤 `mypy`를 돌려 실제로 에러가 잡히는지 확인했습니다.**

- `AppContext`에 `category_service: CategoryService`, `budget_service: BudgetService`처럼 서로 다른 타입을 명시해뒀습니다.
- 두 인자의 자리를 일부러 바꾼 뒤 `mypy budget_app`을 실행하니, 실제로 `error: Argument "category_service" to "AppContext" has incompatible type "BudgetService"; expected "CategoryService"`가 출력됐습니다.
- 되돌린 뒤 다시 실행하면 `Success: no issues found in 20 source files`가 출력됩니다.
- 이걸로 타입 힌트가 "이 자리엔 이 타입만 와야 한다"는 계약을 검증 도구가 실제로 강제할 수 있다는 걸 확인했습니다 — 다만 이는 `mypy` 같은 별도 도구를 돌려야 잡히는 것이고, 파이썬 실행 자체가 막아주는 건 아닙니다.

**Q. JSONL과 CSV 중 왜 JSONL을 선택했나요?**
**한 줄에 값 하나만 있는 CSV보다, 한 줄에 객체 하나가 담긴 JSONL이 `tags` 같은 리스트 필드를 다루기 쉬워서 선택했습니다.**

- CSV는 모든 값이 문자열이라 리스트인 `tags`를 넣으려면 별도 구분자(콤마 등)로 인코딩/디코딩해야 합니다. JSONL은 JSON이라 리스트를 그대로 저장할 수 있습니다.
- 나중에 필드가 추가돼도 JSONL은 각 줄이 독립된 객체라 옛날 줄에 없는 필드를 선택적으로 다루기 자연스럽습니다. CSV는 헤더가 고정이라 유연성이 떨어집니다.
- 다만 CSV가 유리한 지점도 있습니다 — 엑셀에서 바로 열어볼 수 있어 사람이 읽기 편합니다. 그래서 내부 저장은 JSONL, 외부와 주고받는 "교환 형식"인 import/export는 CSV로 나눠서 각각의 장점을 살렸습니다.

**Q. 거래가 10만 건으로 늘어난다면 병목이 어디이고, 어떻게 개선할까요?**
**실제로 10만 건을 만들어 측정해보니, "새 id 채번"과 "update/delete의 전체 재작성" 2곳이 병목이었습니다.**

- 실측치: `add()` 411ms, `list_recent()` 376ms, `update()` 1,159ms, `delete()` 1,129ms, `update` 100번 연속 실행 시 총 114초 (자세한 수치는 아래 "대용량 처리 / 성능 병목 분석" 참고).
- 원인1: `next_id()`가 새 거래를 추가할 때마다 전체 파일을 훑어서 최대 id를 찾습니다 — 10만 건에서는 이것만으로 0.4초가 걸립니다.
- 원인2: `update()`/`delete()`는 원자적 교체를 위해 매번 전체 파일을 다시 씁니다 — 10만 줄짜리 파일을 건드릴 때마다 1초 이상이 걸리고, 반복하면 그대로 누적됩니다.
- 개선 방향1: 순번 대신 `uuid.uuid4()`(표준 라이브러리)를 쓰면 파일을 훑지 않고도 고유 id를 즉시 만들 수 있습니다 (대신 id가 짧고 읽기 좋은 형태는 포기해야 합니다).
- 개선 방향2: 파일을 월별로 쪼개(`transactions/2024-01.jsonl` 등) 저장하면, update 1건당 재작성 비용이 "전체 건수"가 아니라 "그 달 건수"에만 비례하게 줄어듭니다.
- 근본적 개선: 표준 라이브러리에 포함된 `sqlite3`로 옮기면 인덱스 기반으로 update/delete가 대수 시간(logarithmic)이 되어, 파일 통째 재작성 자체가 필요 없어집니다 — "표준 라이브러리만 사용" 제약 안에서도 가능한 가장 확실한 해결책입니다.

**Q. import CSV에 일부 깨진 행이 섞이면 어떻게 처리해 사용자 신뢰를 지킬까요?**
**전부 되돌리는 롤백 대신, 유효한 행은 저장하고 실패한 행은 건수로 알려주는 부분 성공 방식을 택했습니다.**

- 롤백을 안 쓴 이유: 1000줄 중 1줄이 깨졌다고 999줄까지 전부 버리면, 사용자가 999줄을 처음부터 다시 입력해야 하는 부담이 더 큽니다.
- 무조건 저장을 안 쓴 이유: 잘못된 행까지 검증 없이 저장하면 데이터가 조용히 오염됩니다. 그래서 각 행을 `add()`의 검증 로직에 그대로 통과시키고, 실패하면 건너뜁니다.
- 현재 한계(솔직히 인정할 부분): 지금은 `imported=3, skipped=2`처럼 건수만 알려주고, 몇 번째 줄이 왜 실패했는지는 알려주지 않습니다. 사용자가 어떤 행을 고쳐야 할지 알 수 없다는 점은 신뢰 관점에서 아쉬운 지점입니다.
- 개선 방향: `import_csv()`가 건수 대신 `(imported_count, [(줄번호, 실패사유), ...])` 형태로 반환하도록 바꾸면 "3번째 줄: 날짜 형식 오류"처럼 구체적으로 알려줄 수 있습니다.

## 대용량 처리 / 성능 병목 분석

`transactions.jsonl`에 실제로 10만 건을 채운 뒤 각 연산 1회를 측정했습니다.

| 연산                  | 소요 시간 | 원인                                                   |
| --------------------- | --------- | ------------------------------------------------------ |
| `add()` 1건           | 411 ms    | `next_id()`가 전체 파일을 훑어 최대 id를 찾음          |
| `list_recent()`       | 376 ms    | `heapq.nlargest`가 전체를 한 번 훑음 (메모리는 제한됨) |
| `update()` 1건        | 1,159 ms  | 10만 건 전체를 임시 파일에 다시 씀                     |
| `delete()` 1건        | 1,129 ms  | 위와 동일                                              |
| `update()` 연속 100회 | 114초     | 매 호출마다 전체 재작성 비용이 그대로 누적             |

같은 파일에 대해 `search`/`summary`는 조건에 맞는 결과나 집계값만 메모리에 남기므로 이 표에는 포함하지 않았습니다 — 이 둘이야말로 스트리밍의 이점이 가장 뚜렷하게 드러나는 연산입니다. 병목 2곳(`next_id()`, 전체 재작성)에 대한 개선 방향은 바로 위 "학습 목표 & 설명"의 해당 문항에 정리했습니다.

## 설계 Trade-off

| 항목               | 선택                          | 포기한 대안과 이유                                                          |
| ------------------ | ----------------------------- | --------------------------------------------------------------------------- |
| 저장 포맷          | JSONL                         | CSV는 리스트 필드(tags)를 다루기 번거로워서 포기                            |
| update 방식        | 옵션 기반                     | 대화형은 손 테스트는 편하지만 스크립트로 재현/자동 테스트하기 어려워서 포기 |
| 카테고리 초기화    | 안 A (기본 카테고리 자동생성) | 안 B(등록 강제)는 초기 사용성이 나빠서 포기                                 |
| 카테고리 삭제 정책 | 사용 중이면 차단              | 대체 카테고리 자동 치환은 사용자가 의도치 않은 재분류가 생길 수 있어 포기   |

**최신순 정렬: date 기준 vs id(등록순) 기준**

- id 기준이 알고리즘적으로 더 쌉니다: 파일이 항상 id 오름차순으로 쌓이므로, 파일 끝에서 거꾸로 N줄만 읽으면 전체를 훑지 않아도 됩니다.
- date 기준은 뒤늦게 예전 날짜를 입력하는 상황 때문에 최소 한 번은 전체를 훑어야 합니다 (`heapq`로 메모리는 제한 가능해도 시간은 O(전체 건수)).
- 그럼에도 date를 선택한 결정적 이유는 `import` 기능입니다. 3월 거래를 먼저 넣어 `TX-000001/002`를 받고, 그 다음 1월 거래를 CSV로 뒤늦게 import하면 `TX-000003/004`를 받습니다 — id로 정렬하면 "최신순"인데 1월 거래가 3월 거래보다 위에 뜨는 모순이 생깁니다. 실제로 재현해 확인했습니다.
- 결론: 이 프로젝트 규모(개인 가계부, 수백~수천 건)에서 O(n) 스캔 비용은 체감이 안 될 정도로 작고, "최신순"이라는 이름의 의미를 정확히 지키는 쪽이 더 중요하다고 판단했습니다.

## 기능별 테스트 / 확인 방법

| 확인 항목                                                     | 확인 방법                                                                                               |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| add/list/search/summary/export/import/update/delete 정상 동작 | `python -m unittest discover -s tests -v` (24개) + 위 "CLI 사용법 상세"의 각 명령 직접 실행             |
| 재실행 후 데이터 유지                                         | 아무 `add` 실행 후 터미널을 새로 열어 `list` 재실행 — 그대로 남아있는지 확인                            |
| category 사용 중 삭제 차단                                    | `category remove food`(사용 중이면 차단) vs 미사용 카테고리 삭제(성공) 각각 실행                        |
| budget 사용률/초과 경고                                       | `budget set` 후 `summary`에서 "사용률 N%" 문구 및 초과 시 경고 문구 확인                                |
| CSV 스키마(UTF-8/헤더/컬럼)                                   | `export --out t.csv --month ...` 후 `cat t.csv`로 `date,type,category,amount,memo,tags` 헤더 확인       |
| 스택트레이스 없이 오류+힌트                                   | 존재하지 않는 id로 `update`/`delete` 실행 — `[오류]`/`[힌트]` 두 줄만 출력되고 트레이스백이 없는지 확인 |
| 오류 종료 코드                                                | 위 명령 실행 직후 `echo $?`로 `1` 확인, 필수 옵션 누락 시(예: `summary` 단독 실행) `echo $?`로 `2` 확인 |

## 배운 것 & 마무리

> 이 프로젝트를 통해 답할 수 있게 된 질문: **"데이터가 많아질수록 코드는 왜, 어떻게 달라져야 하는가"**

- **파일 영속화** — JSONL, 원자적 교체(tempfile + os.replace)
- **메모리 효율** — 제너레이터(`yield`), `heapq.nlargest`를 이용한 bounded top-N
- **관심사 분리** — 데코레이터(로그/시간측정/예외처리), 4계층 아키텍처
- **타입 안정성** — 타입 힌트 + `mypy` 정적 검증
- **트레이드오프 사고** — 알고리즘적 최적(id) vs 요구사항이 원하는 의미(date), 부분성공 vs 롤백

## 참고 / 트러블슈팅

- `tests/`는 `budget_app/` 안이 아니라 레포 루트에 있어야 `python -m unittest discover -s tests`가 정상 동작합니다.
- Windows에서는 `python`, macOS에서는 상황에 따라 `python3`가 필요할 수 있어 `--version`으로 3.10 이상인지 먼저 확인하는 걸 권장합니다.
- `mypy`는 실행에는 필요 없는 개발 시 검증 도구입니다 (`pip install mypy`로 별도 설치, 채점 대상 코드에는 포함되지 않습니다).
- README 구조는 `check_readme.py`로 자동 검증했습니다 (`python check_readme.py README.md`).
