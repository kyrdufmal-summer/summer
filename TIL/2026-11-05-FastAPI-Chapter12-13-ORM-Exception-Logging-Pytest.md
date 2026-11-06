# TIL | 2026-11-05 — FastAPI Chapter 12·13: ORM CRUD, 예외 처리, Logging, TestClient, pytest와 PostgreSQL 검증

> **학습 기준일:** 2026-11-05 (실습 및 대화 기록 기준)  
> **과제 저장소:** [fullstack-web-course](https://github.com/kyrdufmal-summer/fullstack-web-course)  
> **과제 커밋:** [808d529](https://github.com/kyrdufmal-summer/fullstack-web-course/commit/808d529)  
> **소스 경로:** `practice/phase02/chapter13/`  
> **검증 원칙:** 확인한 사실 / 원인에 대한 추론 / 추가 검증이 필요한 사항을 구분한다.  
> **보안 원칙:** 비밀번호·토큰·쿠키·Webhook·`.env` 실제 값은 기록하지 않는다(필요 시 `***` 처리).

## 1. 오늘의 목표 및 문제 정의

Chapter 12에서 SQLAlchemy ORM을 통해 Member CRUD를 구현했고, Chapter 13에서는 같은 기능에 **HTTP 오류 계약, Logging, TestClient, pytest 자동 테스트**를 연결했다. 핵심 질문은 단순히 “코드가 돌아가는가?”가 아니라 **“예상하지 못한 상황에서 업무 규칙이 깨질 때 무엇을 관찰하고, 어떻게 재현하며, 무엇으로 복구·재발 방지를 입증할까?”**였다.

특히 다음 혼동을 해소했다.
- Swagger와 pytest가 같은 `/members`를 실행하는데 왜 둘 다 필요한가?
- Router·Schema·Service·Repository·Model·Session 중 실제로 누가 누구를 호출하는가?
- `404`, `409`, `422`는 모두 실패인데 왜 pytest에서는 `PASSED`인가?
- `chapter13_test` 데이터베이스를 만들었는데 왜 FastAPI는 기존 `postgres`를 계속 사용했는가?
- GitHub에 로컬 `phase02` 폴더가 있는데 웹에서는 왜 404가 나왔는가?

## 2. 전체 업무·데이터 흐름

### 2.1 정상 회원가입 (POST 201)

```text
pytest 실행 (test_members.py)
  └─ TestClient.client.post("/members", json=...)
      └─ FastAPI 앱 (app/main.py: 앱 생성·Router 등록)
          └─ Router (app/routers/member_router.py: POST 요청 접수)
              ├─ Pydantic MemberCreate (app/schemas.py: 요청 데이터 형식 검증)
              ├─ Depends(get_db) (app/db.py: 요청용 Session 제공)
              └─ Service (app/services/member_service.py: 중복 가입 정책)
                  ├─ Repository.find_by_email() → PostgreSQL SELECT
                  └─ 중복이 없다면 Repository.create_member()
                      └─ Member ORM Model + SQLAlchemy Session
                          └─ PostgreSQL INSERT → commit
      ← MemberResponse 및 HTTP 201
  ← pytest assert로 status / 응답 값 비교 → PASS 또는 FAIL
```

**정확성 메모:** 위는 이해를 위한 처리 흐름이다. `main.py`는 요청 때마다 재실행되는 것이 아니라 앱 import 시 초기화된다. Schema 검증과 Dependency 준비는 Router 함수 호출 전에 FastAPI가 수행한다. ORM Model은 별도 실행 순서의 서비스가 아니라 테이블 매핑 정의다.

### 2.2 비정상 흐름과 그 원인

- **이메일 형식 오류 → 422:** 보낸 데이터만으로 형식 오류를 판단할 수 있으므로 Pydantic Schema/FastAPI 요청 검증 단계에서 차단. DB 조회가 필요하지 않다.
- **존재하지 않는 회원 → 404:** Repository가 DB에서 조회한 결과가 없다는 사실을 Service가 업무 오류로 해석한다.
- **중복 이메일 → 409:** 이메일 형식은 정상이어도 DB의 기존 회원과 충돌한다. Repository가 기존 이메일을 조회하고 Service가 정책상 가입을 거절한다. DB UNIQUE는 동시 요청 상황에서 최종 중복 방어선이다.
- **처리하지 못한 내부 오류 → 500 가능:** 모든 예외를 200으로 감추거나, 모든 DB 오류를 일괄 409로 변환하면 장애 분류와 복구 의사결정이 왜곡된다.

## 3. 핵심 개념 — 왜 필요한가, 없으면 무슨 사고가 나는가?

| 구성요소 | 쉬운 비유 | 실제 책임 | 제거·오설계 시 가능한 운영 사고 |
|---|---|---|---|
| Swagger UI | 사람이 직접 눌러 보는 시험 창구 | HTTP 요청·응답 수동 탐색 | 반복 검사 누락·사람의 판단 편차 |
| pytest | 자동 시험 실행·채점기 | `test_*` 탐색·실행·PASS/FAIL 보고 | 수정 후 기존 기능 오류(회귀) 미발견 |
| TestClient | 고객 대신 API 호출하는 시험 직원 | 실행 중인 별도 Uvicorn 없이 앱 ASGI 호출 | API 호출 자동화가 번거로움 |
| Schema | 신청서 형식 검사 | 필수값·자료형·이메일 형식 검증 | 잘못된 값이 후속 계층에 유입 |
| Router | 고객 접수 창구 | HTTP 경로·응답 계약·Service 호출 | POST 경로 없으면 405 등 경로 수준 문제 |
| Service | 회원가입 업무 책임자 | 중복 가입·회원 부재 정책 판단 | 규칙 누락·정상 고객까지 가입 거절 |
| Repository | DB 업무 담당 | SQLAlchemy ORM 조회·등록·삭제 | DB 접근 중복·규칙과 SQL 결합 |
| Model | 테이블의 Python 설계도 | `Member` 객체 ↔ `members` 테이블 | 현재 ORM 매핑 불가 또는 오류 |
| Session | DB 작업 상태 관리자 | ORM 객체·트랜잭션 관리 | commit/rollback 경계 불명확 |
| Logging | 사건 일지 | 발생 지점·수준·메시지 기록 | VOC 급증 시 사고 경로 추적 지연 |
| PostgreSQL | 실제 회원 명부 | 데이터 영속 저장·UNIQUE 제약 | 동시 가입 중복, 데이터 무결성 훼손 |

**중요:** pytest와 Swagger는 **서로 다른 DB를 자동으로 선택하지 않는다.** API를 호출하는 도구와, 앱이 어느 DB에 접속하는지를 정하는 연결 설정은 별개다.

## 4. 오늘 실제 진행한 절차와 확인된 증거

### 4.1 Chapter 13 폴더 구성
- Chapter 12의 `app` 구조를 Chapter 13으로 복사해 시작했다.
- 한때 `chapter13/chapter12/app`으로 중첩되어 경로를 바로잡았다.
- `tests/test_members.py`는 `app/`와 같은 수준인 `chapter13/tests/`에 배치했다.
- `__init__.py`는 빈 파일이어도 Python 일반 패키지를 명시할 수 있다는 점을 복습했다.

### 4.2 import 및 앱 초기화 오류 해결
- `MemberPatch` import 오류를 수정해 `IMPORT OK`를 확인했다(이전 Chapter 12 진행).
- Chapter 13 초기에는 `from app.main import app`에서 ImportError 발생: `main.py`에 Logging만 있고 `app = FastAPI(...)`가 없었다.
- 앱 생성 및 `app.include_router(member_router)`을 추가했다.
- 이후 `member_router.py`의 `Session` 타입 import 누락으로 `NameError`가 발생했고 `from sqlalchemy.orm import Session`으로 수정했다.
- **증거:** `python -c "from app.main import app; print('APP IMPORT OK')"` → `APP IMPORT OK`.

### 4.3 업무 논리 오류와 HTTP Contract
- Service 중복 검사 `if existing is not None:`와 `raise HTTPException(status_code=409)`의 들여쓰기를 확인하고 수정했다.
- 들여쓰기가 잘못되면 중복이 없는 정상 고객에게도 409가 반환되는 **논리 오류**가 생길 수 있다.
- `python -m py_compile app/services/member_service.py` 문법 검사 통과. 단, **문법 통과는 업무 규칙 검증이 아니다.**
- 상세 조회 `GET /members/{member_id}`가 없던 상태에서 기본 404 응답 `{"detail":"Not Found"}`가 나와 테스트 실패했다.
- Router와 Service 상세 조회를 연결하자 업무 계약 메시지 `{"detail":"Member not found"}`로 테스트 통과.
- **교훈:** HTTP 상태코드만 같아도 원인이 같다는 뜻은 아니다. 경로 미등록 404와 DB 조회 후 자원 부재 404를 구별해야 한다.

### 4.4 pytest 준비 및 실행
- `python -m pip install pytest httpx` 진행; `pytest 9.2.0` 설치 확인.
- `python -m pytest tests/test_members.py -v` 실행으로 자동 테스트를 반복했다.
- 테스트는 `GET 200 → GET 404 → POST 201 → 중복 POST 409 → 잘못된 member_id 422` 순으로 확장했다.
- 테스트 코드에서 `uuid4()`를 활용해 재실행할 때 이메일 중복 가능성을 낮췄다.

| 실제 테스트 함수 | 확인하는 조건 | 확인된 결과 |
|---|---|---|
| `test_get_members_returns_200` | 200 및 JSON 배열 | PASS |
| `test_get_unknown_member_returns_404` | 없는 회원의 404 및 상세 메시지 | PASS |
| `test_create_member_returns_201` | 신규 가입 201·이름·이메일 | PASS |
| `test_duplicate_email_returns_409` | 1회 가입 201, 같은 이메일 재시도 409 | PASS |
| `test_member_id_validation_returns_422` | 문자 회원번호 422 | PASS |

- **터미널 최종 증거:** `5 passed, 1 warning in 0.72s` (캡처). 다른 실행에서 `5 passed, 1 warning in 0.82s` 확인.
- Warning: `StarletteDeprecationWarning` — `starlette.testclient` 관련 `httpx` 사용 예정 경고. **테스트 실패나 500 오류는 아님.**
- **검증 범위 제한:** 이 다섯 테스트만 통과한 것. PUT/PATCH/DELETE, 동시 요청, 응답 유실, 모든 DB 상태까지 통과한 것은 아니다.

### 4.5 Logging 실제 검증
- `logging.getLogger(__name__)`로 Service logger 작성.
- 중복 이메일 조건에서 `logger.warning("duplicate member registration attempted")` 기록. 이메일·비밀번호 원문을 출력하지 않았다.
- `python -m pytest tests/test_members.py -v --log-cli-level=WARNING` 실행.
- **실제 로그:** `WARNING app.services.member_service:member_service.py:33 duplicate member registration attempted`.
- **의미:** Service의 중복 요청 분기가 실행됐음을 나타내는 증거. 그 자체로 DB 중복 상태의 완전한 증거는 아니다.

### 4.6 별도 테스트 DB 생성·연결
- 처음 설정은 `CONNECTED DB: postgres`. 기존 `postgres.public`에 POST 테스트가 저장될 위험을 발견했다.
- DBeaver에서 `CREATE DATABASE chapter13_test;` 실행.
- `SELECT datname FROM pg_database WHERE datname = 'chapter13_test';` → `chapter13_test` 1행 확인.
- DBeaver에서 기존 연결을 복제해 DB 이름만 `chapter13_test`로 수정, **Connection test: Connected (215 ms)** 확인.
- 새 연결에서 `SELECT to_regclass('public.members');` → 처음엔 `NULL` 확인. 기존 16명 등의 회원 데이터가 자동 복사된 것이 아님.
- 테스트 DB에서 `public.members` 테이블 생성: `member_id` 기본키·자동 증가, `name`, `email UNIQUE`, `age` 필수.
- `app/db.py`의 URL 구성에서 DB 이름을 학습용으로 `"chapter13_test"`로 지정.
- **실제 설정 확인:** `python -c "from app.db import engine; print('CONNECTED DB:', engine.url.database)"` → `CONNECTED DB: chapter13_test`.
- DBeaver에서 `SELECT member_id, name, email, age FROM public.members ORDER BY member_id;` → 테스트 회원 8건 조회(`Test User`, `First` 패턴). 이는 API 테스트가 실제 DB에 INSERT·commit한 결과를 뒷받침한다.
- **위험:** `uuid4()`는 고유 이메일을 만들 뿐 데이터 삭제 기능은 없다. 반복 테스트로 데이터가 누적된다.

### 4.7 GitHub 과제 제출
- 로컬 `practice/phase02`와 달리 GitHub의 `main/practice/phase02` 페이지가 처음에는 404였다. **원인: 아직 원격에 Push되지 않음.**
- `git status`, `git diff --cached --name-only`를 통해 업로드 파일 범위 점검.
- `__pycache__/*.pyc` 등 자동 생성 파일을 스테이징에서 제거하고 Python 소스만 재등록.
- `git commit -m "feat: chapter13 exception logging and pytest tests"`
- `git push origin main` → 성공.
- **실제 커밋:** `808d529`, `10 files changed, 704 insertions(+)`.
- **주의 깊은 사후 확인:** 커밋에는 Chapter 13의 9개 Python 파일 이외에 `practice/phase02/chapter06/main.py` 1개가 함께 포함되었다. 업로드 성공과 제출 범위의 정확성은 별개이며, 기록상 의도하지 않은 범위가 섞였다.

## 5. 오늘의 비정상 운영 시나리오 — 사고 조건, 영향, 증거, 예방

### 사고 A. “처음 가입하는 회원에게 409” 
- **조건:** 중복 검사 `if` 바깥으로 `raise HTTPException(409)`가 빠져 있음.
- **영향:** 정상 고객 가입 실패, 전환율 저하, VOC 증가.
- **증거:** 신규 이메일 POST에 409, DB 중복 조회 0건, Service 분기 조사.
- **예방·검증:** 정상 201과 중복 409를 함께 회귀 테스트. `py_compile`만으로는 불충분.

### 사고 B. “두 고객의 동시 가입”
- **조건:** Service의 중복 조회를 둘 다 통과한 상태에서 동일 이메일 INSERT 경합.
- **영향:** UNIQUE가 없으면 중복 계정 생성 가능; UNIQUE가 있어도 오류 변환이 없으면 500 노출 가능.
- **예방:** DB UNIQUE를 최종 무결성 제약으로 유지하고, 중복 제약의 `IntegrityError`를 구분하여 rollback 후 적절히 409 처리.
- **검증 미실시:** 이번 `test_duplicate_email_returns_409`는 순차 요청이다. 동시성 테스트는 별도 필요.

### 사고 C. “pytest PASS, 그런데 데이터가 틀림”
- **조건:** `GET /members` 테스트가 200과 JSON list 타입만 검사.
- **영향:** 잘못된 회원 조회, 권한 범위 밖의 회원 노출 같은 오류를 놓칠 수 있다.
- **예방:** 특정 테스트 fixture ID/내용, 인증·인가, 타 사용자 데이터 격리까지 assert.

### 사고 D. “테스트는 정상인데 회원이 계속 쌓임”
- **조건:** POST 테스트가 `commit()` 수행, 각 실행에 `uuid4()` 이메일 생성, 데이터 정리 없음.
- **관찰:** 테스트 DB에 8행 누적.
- **영향:** DB 용량·테스트 독립성 문제; 운영 DB에서 실행하면 통계·VOC·후속 처리 오염 가능.
- **예방:** 테스트 전용 DB, 자동 fixture 정리, 적절한 트랜잭션 경계 및 초기화 정책.

### 사고 E. “테스트 DB를 만들어 놓고 기존 DB에 저장”
- **조건:** DBeaver 연결만 변경하고 FastAPI `DATABASE_URL`은 `postgres`를 유지.
- **증거:** `CONNECTED DB: postgres` 출력으로 사전 발견.
- **예방:** 테스트 실행 전 연결 DB assertion, 테스트 전용 계정의 최소 권한, 운영 DB 쓰기 차단.

### 사고 F. “GitHub에 불필요한 파일이 섞임”
- **조건:** `git add .` 또는 기존 스테이징 잔존, 커밋 직전 전체 목록 확인 부족.
- **영향:** 학습 과제 범위 혼합, 불필요한 파일 노출; `.env`가 섞이면 보안 사고.
- **관찰:** 이번 커밋에 chapter06/main.py도 함께 포함.
- **예방:** `.gitignore` 적용, `git diff --cached --name-only`와 `git diff --cached` 최종 점검 후 커밋.

## 6. 기술 개념 다시 연결하기 — Chapter 12에서 Chapter 13으로

- `Member(...)`는 Python 회원 객체 생성; `session.add()`는 저장 대상 등록.
- `flush()`는 SQL을 DB에 보내지만 트랜잭션 확정은 아님.
- `commit()`은 DB 트랜잭션 확정; `rollback()`은 **아직 확정되지 않은 현재 트랜잭션**을 취소.
- `refresh()`는 DB 값을 ORM 객체에 다시 읽어오는 작업이며 매번 필수는 아님.
- Chapter 12 교육 예제에서는 Repository 내부에서 commit/rollback을 수행했다.
- 회사 실무에서 주문·재고처럼 여러 Repository 작업이 원자적으로 성공해야 할 때는 Service/Unit of Work가 **동일 Session의 트랜잭션 경계**를 관리하도록 설계하는 편이 적절하다.
- Chapter 13의 테스트는 이 규칙이 실제 HTTP 응답과 DB 상태에서 유지되는지를 자동으로 확인한다.
- **중요한 함정:** commit이 이미 끝난 DB 변경은 외부에서 단순 rollback하는 것으로 되돌릴 수 없다. 테스트 격리 설계가 별도로 필요하다.

## 7. 회고 — 새롭게 이해한 점과 판단 기준

1. Swagger는 브라우저에서 사람이 API를 직접 호출하는 테스트 화면이며, 실제 쇼핑몰 프론트엔드가 아니다.
2. pytest는 개발자가 미리 작성한 시나리오와 예상값(`assert`)을 자동 수행한다. 자동으로 사고 시나리오를 발견해 주지는 않는다.
3. Logging은 **어떤 분기가 실행됐는지**, DB 조회는 **실제 저장 상태가 무엇인지**, pytest는 **정의된 계약을 충족했는지**를 각각 증명한다.
4. 실패 응답인 404·409·422도 기대한 계약이면 pytest `PASS`다.
5. 좋은 실무 분석은 정상 처리 설명보다 **흐름이 깨지는 경계: 동시성·재시도·응답 유실·부분 성공·잘못된 연결·테스트 데이터 오염**을 포착하는 데서 출발한다.

### 개인 학습 원칙
> 전체 흐름 → 왜 이 계층이 맡는가 → 다른 곳에 두면 무엇이 깨지는가 → 실제 운영 사고 조건 → 고객·회사 손실 → 로그/DB/API 증거 → 예방·복구 설계 → 재현 테스트.

## 8. 다음 과제 / 미검증 항목

- [ ] 테스트 전용 DB를 **`.env.test` 또는 별도 설정**으로 안전하게 선택하도록 분리(현재 DB명 하드코딩은 학습용).
- [ ] 테스트 실행 시 `current_database() == 'chapter13_test'` 등 fail-fast 검증.
- [ ] 테스트 데이터 자동 정리 및 반복 실행해도 결과가 일정한 fixture 구성.
- [ ] POST 중복의 **동시성 시나리오**와 UNIQUE `IntegrityError`의 정확한 409 변환 확인.
- [ ] PUT/PATCH/DELETE 회귀 테스트 및 PATCH 생략/명시적 `null` 계약 확인.
- [ ] 회원조회 권한 및 데이터 격리 테스트.
- [ ] API·DB·로그·테스트 결과를 함께 기록하는 제출용 증빙 체계.
- [ ] GitHub 커밋 `808d529`에 포함된 Chapter 06 파일의 필요성 검토.
- [ ] `StarletteDeprecationWarning` 의존성 버전 정리(기능 실패와 구분).

## 9. 직접 확인한 근거 및 참고 자료

- [Chapter 13 과제 소스](https://github.com/kyrdufmal-summer/fullstack-web-course/tree/main/practice/phase02/chapter13)
- [TestClient/pytest 테스트 원본](https://github.com/kyrdufmal-summer/fullstack-web-course/blob/main/practice/phase02/chapter13/tests/test_members.py)
- [Service 예외 및 Logging 소스](https://github.com/kyrdufmal-summer/fullstack-web-course/blob/main/practice/phase02/chapter13/app/services/member_service.py)
- [DB Session·테스트 DB 설정](https://github.com/kyrdufmal-summer/fullstack-web-course/blob/main/practice/phase02/chapter13/app/db.py)
- [과제 Commit 808d529](https://github.com/kyrdufmal-summer/fullstack-web-course/commit/808d529)
- 사용자 제공 터미널·DBeaver 스크린샷: `5 passed, 1 warning`, WARNING 로그(`member_service.py:33`), `chapter13_test` 회원 8건 조회, Git Push 성공 확인.
- 강의 기반: 아토믹데브, 「12강. SQLAlchemy ORM 기반 CRUD — Repository / Session / Commit / Rollback」, 「13강. 예외 처리·Logging·TestClient — 오류를 추적하고 다시 검증하기」 (2026-10-29 강의 내용, 사용자 제공).

---

**최종 판정:** Chapter 13의 확인된 다섯 가지 API 자동 테스트, 중복 요청 WARNING 로그, 테스트 DB 저장 검증, GitHub Push **완료**. 동시성·데이터 정리·전체 CRUD 회귀 테스트는 **추가 과제**로 남는다.
