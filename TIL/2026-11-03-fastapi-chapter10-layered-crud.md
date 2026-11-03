# 2026-11-03 TIL — FastAPI Chapter 10 계층형 CRUD 구조화와 HTTP 검증

> 학습 범위: **오늘 대화에서 실제 진행·확인한 내용만 기록**. 개인 로컬 소스 전체를 GitHub에서 직접 읽은 것은 아니며, 코드 작성 여부는 사용자의 보고와 VS Code/Swagger/터미널 캡처를 기준으로 함.
>
> 상태: **GET/POST 기능 및 HTTP 검증 완료 / PUT·PATCH·DELETE 구현 후 Swagger 등록 확인 / PUT·PATCH·DELETE 실행 검증 대기**.
>
> 보안: 비밀번호, .env 값, 토큰, 웹훅 URL 등 비밀 설정은 기록하지 않으며 표기할 경우 `***`로 마스킹.

## 1. 오늘의 핵심 요약

- Chapter 10의 목표는 **파일 수를 늘리는 것이 아니라 책임을 분리**하는 것.
- **Request:** Client → Router → Service → Repository → PostgreSQL.
- **Response:** PostgreSQL → Repository → Service → Router/FastAPI → Client.
- `Schema`는 별도 요청 처리 서버가 아니라 Pydantic으로 입력을 검증하고 출력 형태를 정의하는 데이터 계약이다.
- 학습 비유는 삼성전자 서비스센터의 가상 업무 프로세스(실제 회사 내부 설계에 대한 주장은 아님): 접수 상담원(Router), 업무 판단 책임자(Service), 전산 기록 담당자(Repository), 기록 보관소(DB).
- 실무상 **코드 작성 순서**와 **실행 순서**는 다르다. 교수님 예제의 작성 순서는 DB → Schema → Repository → Service → Router → Main이며, Service 우선 설계도 가능하나 요청 실행 경로는 유지된다.

## 2. 문제 정의와 학습 동기

Chapter 06~09에서는 Endpoint 내부에 HTTP, 업무 규칙, SQL, DB 연결이 섞일 수 있었다. 이 경우 기능이 늘어날수록:
1. SQL과 업무 판단의 책임 경계가 모호해진다.
2. 이메일 중복 검사 등의 정책이 여러 Endpoint에 중복된다.
3. 장애 수정 시 영향 범위를 추적하기 어렵다.
4. 기존 API 계약을 유지하며 리팩터링하기 어려워진다.

**완료 기준:** Router/Service/Repository/Schema/DB의 책임을 설명할 수 있고, 구조를 바꾼 뒤에도 동일한 HTTP API 동작을 확인한다.

## 3. 용어와 역할 — 한 줄 / 필요 이유 / 없으면

| 파일·계층 | 한 줄 역할 | 필요한 이유 | 없다면(대체 구현이 없을 때) |
|---|---|---|---|
| `app/main.py` | FastAPI 앱 생성 및 Router 등록 | API를 하나의 앱에 조립 | 해당 API가 앱에 등록되지 않음 |
| Router `app/routers/members.py` | HTTP 요청 접수, Service 호출, 응답 계약 연결 | URL/메서드와 업무를 연결 | 요청을 받아줄 엔드포인트가 없음 |
| Service `app/services/member_service.py` | 업무 규칙 판단 및 처리 순서 조율 | 중복·404·409 등을 한곳에서 결정 | 정책이 여러 계층으로 흩어질 수 있음 |
| Repository `app/repositories/member_repository.py` | SQL로 DB 조회·등록·수정·삭제 | 데이터 접근을 한곳에서 관리 | SQL이 Router·Service 등에 흩어질 수 있음 |
| `app/db.py` | PostgreSQL 연결 함수 제공 | 연결 설정 재사용 | 파일마다 연결을 재구현해야 할 수 있음 |
| Schema `app/schemas.py` | 입력 형식 검증, 출력 정보 형식 지정 | 잘못된 입력 차단 및 계약 통일 | 검사·출력 규칙을 따로 구현해야 함 |
| PostgreSQL | 실제 데이터 보관 | 영속적인 데이터 저장 | 별도 영속 저장 수단이 없으면 데이터 유지 불가 |
| `__init__.py` | 폴더를 일반 Python 패키지로 명시 | import/패키지 구조 명확화 | Python 3.3+에서는 namespace package로 동작할 수도 있음 |

추가 비교: **Java DTO + Bean Validation ≈ Python Pydantic Schema**. Java interface는 데이터 계약 자체보다는 메서드/동작 계약에 가까움.

## 4. 학습 환경 및 프로젝트 구조

- Windows PowerShell, VS Code, Python 가상환경 `(.venv)`.
- 작업 위치(캡처 확인): `C:\stage_1\dev\fullstack-web-course\practice\phase02\chapter10`.
- DB: PostgreSQL; 실제 테이블은 `public.members`, 키 컬럼은 **`id`**. 교수님 원문의 `member_id`를 실습 DB에 맞춰 `id`로 사용.

```text
chapter10/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI 조립
│   ├── db.py                     # DB 연결
│   ├── schemas.py                # Pydantic 데이터 계약
│   ├── routers/
│   │   ├── __init__.py
│   │   └── members.py            # HTTP 엔드포인트
│   ├── services/
│   │   ├── __init__.py
│   │   └── member_service.py     # 업무 규칙
│   └── repositories/
│       ├── __init__.py
│       └── member_repository.py  # SQL
├── common/
│   └── db.py                     # 과거 실습 연결 코드(유지)
├── .env                          # 비밀정보, Git 커밋 금지
└── .gitignore
```

### `common/db.py` vs `app/db.py` 결정

기존 `common/db.py`에 `get_connection()`, `check_connection()`, `fetch_members()`가 있었음. 그러나 이번 수업에서는 교수님 기준 `app.db` import 구조에 맞춰 **`app/db.py`를 별도 구현**하기로 결정함. 기존 `common/db.py`는 보존.

실무에서는 중복 연결 구현보다 공통 모듈 재사용이 나을 수 있으나, 이번 결정은 수업 구조의 재현을 우선. 기존 `common/db.py`의 `print(DB_HOST, DB_PORT, DB_NAME, DB_USER)`는 불필요한 접속 정보 출력이므로 추후 제거 권장.

## 5. 실제 수행한 단계와 증거

### STEP 01 — DB 연결 분리 및 import 경로 해결

`app/db.py`에서 `load_dotenv()`로 설정 로딩, `psycopg.connect(...)`를 반환하는 `get_connection()` 정의. 민감 설정 원문은 TIL에 기록하지 않음.

첫 테스트는 `phase02` 폴더에서 실행하여:
```text
ModuleNotFoundError: No module named 'app'
```
발생. 실행 위치를 `chapter10`으로 바꿈:
```powershell
cd chapter10
python -c "from app.db import get_connection; conn = get_connection(); print('DB 연결 성공'); conn.close()"
```
**실제 출력:** `DB 연결 성공`. import 탐색 위치가 중요한 이유를 확인.

### STEP 02 — Pydantic Schema 작성 및 거부 검증

`app/schemas.py`에 네 종류 정의:
- `MemberCreate`: POST 신규 회원, `name` 1~100자, `EmailStr`, `age` 0~150.
- `MemberUpdate`: PUT 전체 수정, 세 항목 모두 입력.
- `MemberPatch`: PATCH 부분 수정, 필드 생략 가능.
- `MemberResponse`: `id`, `name`, `email`, `age`를 응답 형식으로 지정.

단위 검증:
```powershell
python -c "from app.schemas import MemberCreate; MemberCreate(name='Kim', email='kim@example.com', age=-5)"
```
**실제 결과:** `ValidationError` / `age` / `Input should be greater than or equal to 0` / `input_value=-5`. 이 빨간 글씨는 **의도된 검증 실패**이며 코드 결함이 아님. 이 명령은 HTTP 요청이 아니므로 HTTP 422 자체는 발생하지 않음.

### STEP 03~04 — Repository와 Service 분리

Repository 함수:
- `find_all()`: 회원 목록 `SELECT ... ORDER BY id`, `fetchall()`.
- `find_by_id(id)`: 특정 회원 `SELECT ... WHERE id = %s`, `fetchone()`.
- `exists_by_email(email, exclude_member_id=None)`: 중복 이메일 여부, `SELECT 1`, 결과는 `True/False`.
- `create(data)`: 고객 **한 명의** 정보 `INSERT ... RETURNING` 후 `commit()`.
- 이후 `update`, `patch`, `delete` 구현.

Service 함수:
- `get_members()`: Repository 전체 조회 위임.
- `get_member(id)`: Repository 조회 후 회원이 없으면 404.
- `create_member(data)`: 이메일 중복 여부 검사 후 409 또는 저장 요청.
- 이후 `update_member`, `patch_member`, `delete_member` 구현.

중요한 오해 해결: `create_member(data)`의 `data`는 **고객 1명의 요청 데이터**이지 수백만 행의 DB 전체가 아님. `exists_by_email()`은 일치 여부를 질문하며, DB 내부 처리량은 인덱스 등에 영향받음.

실제 터미널 확인:
```powershell
python -c "from app.services.member_service import get_members; print(get_members())"
python -c "from app.services.member_service import get_member; print(get_member(1))"
python -c "from app.services.member_service import get_member; print(get_member(99999))"
```
- 회원 목록이 딕셔너리 목록으로 출력됨(당시 **7건**).
- 특정 회원 `id=1` 조회: `{'id': 1, 'name': 'Kim', 'email': 'kim@example.com', 'age': 25}`.
- `99999` 조회: `fastapi.exceptions.HTTPException: 404: Member not found`.
- 이는 Service 직접 호출 테스트이며, HTTP 요청 검증은 별도 수행.

### STEP 05~08 — Router와 FastAPI 앱 연결

`app/routers/members.py`에 `APIRouter(prefix="/members", tags=["members"])`, GET 전체/상세, `response_model` 등록. `app/main.py`에 `app = FastAPI()`, `app.include_router(members.router)` 작성.

```powershell
python -m uvicorn app.main:app --reload
```
서버 로그: `Uvicorn running on http://127.0.0.1:8000`, `Application startup complete.`. Swagger: `http://127.0.0.1:8000/docs`.

확인한 HTTP 테스트:
- `GET /members` → `200 OK`.
- `GET /members/1` → `200 OK` 및 id=1 회원정보.
- `GET /members/9999` → `404 Not Found`.

### STEP 09~11 — POST 생성, 이메일 중복 거절, 422 검증

**이메일 존재 여부 직접 테스트:**
```powershell
python -c "from app.repositories.member_repository import exists_by_email; print(exists_by_email('kim@example.com'))"
python -c "from app.repositories.member_repository import exists_by_email; print(exists_by_email('notregistered99999@example.com'))"
```
출력 각각 **`True` / `False`**.

**정상 신규 생성(Service 직접 호출):**
```powershell
python -c "from app.schemas import MemberCreate; from app.services.member_service import create_member; data=MemberCreate(name='TestUser', email='testuser20261103@example.com', age=25); print(create_member(data))"
```
결과: `id=11` 생성 확인.

**중복 가입(Service 직접 호출):** 기존 이메일 재사용 → `HTTPException: 409: Email already exists` 확인.

**Swagger HTTP 레벨 검증:**
- `POST /members` 신규 회원(예: '세종대왕', `kingsejong@example.com`, 68) → **201 Created**, `id=12` 반환.
- 동일 이메일 재요청 → **409 Conflict**, `{"detail": "Email already exists"}`.
- 잘못된 입력 `{"name":"TestUser","email":"invalid-email","age":-5}` → **422 Unprocessable Content** 서버 로그 확인.
- 직접 Pydantic 검증과 FastAPI HTTP 422 검증은 구분해야 함.

### PUT / PATCH / DELETE 일괄 구현

마지막에 Repository/Service/Router의 **3개 파일 전체 교체 코드**를 작성하고 붙여넣음. Swagger에서 다음 **6개 API 등록**을 눈으로 확인함:
- GET `/members`
- POST `/members`
- GET `/members/{id}`
- PUT `/members/{id}`
- PATCH `/members/{id}`
- DELETE `/members/{id}`

수정·삭제 테스트에 사용할 임시 회원을 생성:
```json
{"name":"UpdateTest","email":"updatetest20261103@example.com","age":25}
```
**실제 Swagger 결과: 201 Created / `id=13`**.

마지막 시점: `PUT /members/13` 전체 수정 요청을 준비한 상태. 예정된 입력:
```json
{"name":"UpdateComplete","email":"updatecomplete20261103@example.com","age":30}
```
**이 PUT 요청의 실행 및 응답은 아직 확인하지 않았으므로 성공이라고 기록하지 않음.** PATCH·DELETE 역시 Swagger에 보이는 것만 확인됐고 실행 검증은 미완료.

## 6. 검증표 — 확인과 미확인 구분

| 항목 | 증거 | 상태 |
|---|---|---|
| PostgreSQL 연결 | `DB 연결 성공` | ✅ 확인 |
| Pydantic 음수 나이 거절 | `ValidationError` | ✅ 확인 |
| Service 전체 회원 조회 | 회원 딕셔너리 목록 | ✅ 확인 |
| Service 상세 조회 | id=1 결과 | ✅ 확인 |
| Service 없는 회원 조회 | 예외 404 | ✅ 확인 |
| 이메일 조회 | True / False | ✅ 확인 |
| 직접 회원 생성 | id=11 | ✅ 확인 |
| 직접 중복 가입 | 예외 409 | ✅ 확인 |
| HTTP GET 전체 / 상세 | 200 / 200 | ✅ 확인 |
| HTTP GET 없는 회원 | 404 | ✅ 확인 |
| HTTP POST 정상 / 중복 | 201 / 409 | ✅ 확인 |
| HTTP POST 잘못된 입력 | 422 로그 | ✅ 확인 |
| PUT·PATCH·DELETE Swagger 등록 | 세 API 목록 표시 | ✅ 확인 |
| PUT 실제 DB 수정 및 200 | 아직 요청 실행 결과 없음 | ⏳ 미검증 |
| PATCH 일부 수정 및 200 | 아직 요청 실행 결과 없음 | ⏳ 미검증 |
| DELETE 삭제 및 204 | 아직 요청 실행 결과 없음 | ⏳ 미검증 |
| PUT/PATCH/DELETE 404·409·422 경계 | 실행 결과 없음 | ⏳ 미검증 |
| 테스트 후 DB 상태 조회 | id=13 생성 응답 이외 직접 재조회 없음 | ⏳ 일부 미검증 |
| .env Git 추적 여부 | 실제 Git 추적 검사 없음 | ⏳ 미검증 |

## 7. 남은 과제와 실무 개선 포인트

1. 테스트 회원 `id=13`으로 PUT 전체 수정 수행 → 응답 200과 변경된 3개 필드 확인.
2. 같은 회원으로 PATCH 한 필드만 수정 → 나머지 필드 불변 확인.
3. 해당 테스트 회원만 DELETE → 204 확인, GET으로 다시 조회해 404 확인.
4. 존재하지 않는 대상에 대한 PUT/PATCH/DELETE 404, 수정 중 이메일 중복 409, 잘못된 입력 422를 회귀 테스트.
5. 작업 전후 PostgreSQL 상태 재조회해 실제 변경·삭제 여부 확인. **다른 회원 데이터는 삭제 금지**.
6. **동시성 위험:** `SELECT 1` 중복 확인만으로 동시 가입을 완전 방지할 수 없음. 이메일 `UNIQUE` 제약 및 DB 무결성 오류 처리가 필요.
7. **트랜잭션 소유권:** 강의 예제의 Repository 단위 `commit()`은 단일 CRUD 학습에서는 편하지만, 주문·재고 등 복수 변경은 Application/Service가 같은 DB 트랜잭션의 `commit/rollback`을 관리해야 함.
8. **대용량 조회:** `find_all()`은 모든 회원을 반환하므로, 실무 대량 데이터에서는 페이지네이션과 인덱스 검토 필요.
9. **비밀정보 보호:** `.env`를 `.gitignore`로 관리하고 로그에서 접속 정보 출력을 제거. Git 추적 여부도 확인 필요.
10. **회귀 테스트:** 겉으로 보이는 API 계약(경로, 상태코드, Request/Response)을 유지한 채 내부 책임이 분리됐는지 점검.
11. `common/db.py`와 `app/db.py`의 장기적인 중복 연결 설정을 정리하고, 교수님 수업 구조가 끝난 후 공통 모듈화 검토.

## 8. 오늘 배운 장애 원인과 해결

- **`ModuleNotFoundError: No module named 'app'`**: `phase02`에서 실행한 import 탐색 경로 문제. `cd chapter10`으로 해결.
- **빨간 `ValidationError`**: `age=-5`를 일부러 넣은 정상 검증 실패.
- **빨간 404/409**: 존재하지 않는 회원·중복 이메일을 거부하도록 의도한 예외. 성공 기준은 적절한 코드와 메시지.
- **터미널 출력이 지워지지 않음**: `cls`는 과거 출력만 지우며 코드 상태를 바꾸지 않음.
- **Swagger 화면 vs 실행 결과**: API가 목록에 보인다는 것은 Router **등록 확인**, HTTP 요청 성공 및 DB 변경의 증거는 아님.

## 9. 암기 문장과 자가 점검

> **Main은 조립, Router는 접수, Schema/Pydantic은 입력 검사·응답 형식, Service는 판단, Repository는 SQL, db.py는 연결, PostgreSQL은 저장.**

자가 점검 질문:
1. 왜 작성 순서(Repository 먼저)와 실행 순서(Service → Repository)가 다른가?
2. `create_member(data)`의 `data`는 회원 1명인가, DB 전체인가?
3. `Schema` 형식 오류 422와 `Service` 이메일 중복 409는 어떻게 다른가?
4. 왜 `SELECT 1`로 중복을 확인해도 DB UNIQUE 제약이 필요한가?
5. Swagger 등록만으로 PUT/DELETE 성공을 확정할 수 없는 이유는?

## 10. 출처와 증거 범위

- 학습 근거: 사용자 제공 아토믹데브 블로그 「10강. Backend 구조화 — Router / Service / Repository / Schema / DB」 (2026-10-29 게시, Chapter 10 교수님 자료).
- 실행 증거: 2026-11-03 대화에 사용자가 첨부한 VS Code/PowerShell/Swagger 스크린샷과 확인 메시지. TIL에는 캡처 내용을 요약했으며 실제 이미지 파일을 GitHub로 업로드하지 않음.
- 외부 웹 검증은 수행하지 않았고, 위 개발 성과는 **사용자 로컬 환경**에서 확인된 것임.
