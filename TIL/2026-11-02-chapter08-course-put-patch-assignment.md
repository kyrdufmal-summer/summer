# Chapter 08 독립 실습 — Course PUT/PATCH + PostgreSQL 검증

> **2026-11-02 | FastAPI · Pydantic · psycopg · PostgreSQL · Swagger · DBeaver**  
> 제출 목적: Chapter 08 독립 실습 과정 및 확인된 실행 증거 기록  
> **증거 구분:** 아래 **PASS**는 대화 중 실제 Swagger/DBeaver 화면으로 확인한 결과입니다. **NOT TESTED**는 실행 증거가 없어 통과로 표시하지 않았습니다.  
> **캡처 원본:** 별도 첨부 `chapter08-course-evidence-2026-11-02.zip` (GitHub 문서에는 아직 이미지 파일을 업로드하지 못했으므로 첨부 ZIP을 함께 제출해야 함).

## 1. 학습 목적

- `PUT /courses/{course_id}`: 강의의 `title`, `level` 전체 수정. 누락 필드는 Pydantic이 거절.
- `PATCH /courses/{course_id}`: 전달된 필드만 수정, 생략한 필드는 보존.
- 빈 PATCH `{}`는 400, 명시적 `null`은 422로 처리.
- PostgreSQL의 실제 UPDATE 수행을 Swagger 응답·DBeaver SELECT·GET 재조회로 확인.
- SQL 값은 `%s` 플레이스홀더와 파라미터로 전달해 문자열 직접 결합 방지.

## 2. 개발 환경 및 작업 파일

- Windows / VS Code / Python 가상환경 `.venv`
- FastAPI + Pydantic + psycopg + PostgreSQL + DBeaver
- 프로젝트: `phase02/chapter08/courses.py`
- 공통 DB 연결: `phase02/common/db.py`의 `get_connection()`
- 실행 위치: `phase02`
- 실행 명령: `python -m uvicorn chapter08.courses:app --reload`
- Swagger: `http://127.0.0.1:8000/docs`
- 테이블: `public.courses(id SERIAL PRIMARY KEY, title VARCHAR(100) NOT NULL, level INTEGER NOT NULL)`

> 개인정보, DB 비밀번호, API 키, 토큰, Webhook, .env 값은 기록하지 않음. 실제 DB 연결 정보는 코드에 포함하지 않고 `common/db.py`를 사용.

## 3. DB 초기 준비 — 실행 확인

### 테이블 존재 여부 확인

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name = 'courses'
ORDER BY table_schema;
```

최초 조회 0행을 확인하여 실습용 테이블 생성.

```sql
CREATE TABLE public.courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL
);
```

DBeaver에서 CREATE TABLE 실행 로그 확인.

```sql
INSERT INTO public.courses (title, level)
VALUES ('Database',1), ('Frontend',2), ('FastAPI',2);

SELECT id, title, level
FROM public.courses
ORDER BY id;
```

INSERT `Updated Rows: 3` 및 조회 결과 확인:

| id | title | level |
|---:|---|---:|
| 1 | Database | 1 |
| 2 | Frontend | 2 |
| 3 | FastAPI | 2 |

증거: `01-create-table.png`, `02-initial-courses.png`.

## 4. API 설계 및 핵심 코드

**응답 계약:** `CourseResponse(id: int, title: str, level: int)`  
**PUT 모델:** `CourseUpdate(title: str, level: int)`, 제목 1~100글자, 난이도 1~5  
**PATCH 모델:** `CoursePatch(title: str | None = None, level: int | None = None)` + 명시적 null 거부 검증.

```python
from pydantic import BaseModel, Field, model_validator

class CourseResponse(BaseModel):
    id: int
    title: str
    level: int

class CourseUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    level: int = Field(ge=1, le=5)

class CoursePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    level: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def reject_explicit_null(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
```

**GET:** `GET /courses/{course_id}` → `SELECT ... WHERE id = %s`, 없으면 404.  
**PUT:** `UPDATE public.courses SET title = %s, level = %s WHERE id = %s RETURNING id,title,level`.  
**PATCH:** `model_dump(exclude_unset=True)`로 실제 전달된 필드만 추출; `{}`일 때 400; 허용 컬럼 `title`, `level`만 SET 절 생성; 값은 SQL 파라미터로 바인딩; `UPDATE ... RETURNING` 결과가 없으면 404.  
**트랜잭션:** `with get_connection() as conn`의 정상 종료 시 commit, 예외 시 rollback.  
**유의:** 허용 컬럼 목록(화이트리스트)을 사용해야 동적 SQL의 식별자 삽입 위험을 줄일 수 있음.

## 5. 실제 실습 결과 — 검증 증거

| ID | 테스트 | 요청 / 검증 | 실제 확인 결과 | 상태 | 캡처 |
|---|---|---|---|---|---|
| TC-01 | DB 초기 3건 | `SELECT ... ORDER BY id` | 3건 일치 | **PASS** | `02-initial-courses.png` |
| TC-02 | GET 정상 조회 | `GET /courses/3` | 200, FastAPI / level 2 | **PASS** | `03-get-before-put.png` |
| TC-03 | PUT 전체 수정 | `PUT /courses/3`, `{"title":"FastAPI Advanced","level":3}` | 응답 id 3, title FastAPI Advanced, level 3 | **PASS** | `04-put-response.png` |
| TC-04 | PUT DB 검증 | `SELECT ... WHERE id = 3` | 사용자가 DB 조회 결과 일치를 보고함 | **PASS (사용자 확인)** | 화면 캡처 없음 |
| TC-05 | PUT 이후 GET 재조회 | `GET /courses/3` | 200, FastAPI Advanced / level 3 | **PASS** | `05-get-after-put.png` |
| TC-06 | PATCH API 등록 | Swagger GET·PUT·PATCH 표시 | 3개 라우트 확인 | **PASS** | `06-routes.png` |
| TC-07 | PATCH 일부만 수정 | `PATCH /courses/2`, `{"level":4}` | 200, id 2, title Frontend 유지, level 4 | **PASS** | `07-patch-response.png` |
| TC-08 | PATCH DB 검증 | `SELECT ... WHERE id=2` | id 2, Frontend, 4 | **PASS** | `08-patch-db.png` |
| TC-09 | PATCH 이후 GET 재조회 | `GET /courses/2` | 200, Frontend, 4 | **PASS** | `09-get-after-patch.png` |
| TC-10 | 빈 PATCH | `PATCH /courses/2`, `{}` | 400, At least one field is required | **PASS** | `10-empty-patch-400.png` |
| TC-11 | explicit null | `PATCH /courses/2`, `{"level":null}` | 422, level cannot be null | **PASS** | `11-explicit-null-422.png` |
| TC-12 | 없는 ID PATCH | `PATCH /courses/999` | **실행 증거 없음** | **NOT TESTED** | — |
| TC-13 | PUT 필수 필드 누락 | `PUT /courses/2`, `{"level":3}` | **실행 증거 없음** | **NOT TESTED** | — |
| TC-14 | 잘못된 타입 | `PATCH /courses/2`, `{"level":"abc"}` | **실행 증거 없음** | **NOT TESTED** | — |
| TC-15 | 범위 외 난이도 | `PATCH /courses/2`, `{"level":9}` | **실행 증거 없음** | **NOT TESTED** | — |

### 5.1 PATCH 전후 근거

```json
// PATCH /courses/2 요청
{"level": 4}

// 실제 Swagger 응답 (200) / DB 조회 / GET 재조회에서 확인
{"id": 2, "title": "Frontend", "level": 4}
```

**판정:** 요청하지 않은 `title`이 변경되지 않았으므로 부분 수정 요구사항 충족.

### 5.2 빈 PATCH와 명시적 null의 차이

- `{}`: 요청 본문은 있으나 수정 필드가 없어 API 로직에서 **400**.
- `{"level":null}`: 필드를 보냈지만 값이 null이므로 Pydantic validator에서 **422**.
- 명시적 null은 FastAPI가 API 함수를 실행하기 전에 거절하므로, DB UPDATE를 수행하지 않음.

### 5.3 주의사항: SQL 직접 실행과 API 실행은 다름

실습 도중 DBeaver에서 별도로 `UPDATE public.courses SET level=4 WHERE id=3`을 직접 실행했고 `Updated Rows:1`을 확인함. 이는 **FastAPI PATCH 성공의 근거가 아님**. PATCH 성공 증거는 별도로 **2번 강의에 대한 Swagger 200 + DB 조회 + GET 재조회**로 확보함.

## 6. 현업 관점: 실패를 막는 이유

| 통제 | 빠졌을 때 위험 |
|---|---|
| `WHERE id=%s` | 대상 이외의 강의까지 일괄 변경 |
| `CourseUpdate` 필수 필드 | 전체 수정 요청 계약 불일치 |
| `exclude_unset=True` | 보내지 않은 필드의 의도치 않은 덮어쓰기 |
| explicit null 거부 | 필수 정보가 NULL로 바뀌거나 DB 오류 |
| Parameterized Query | SQL 값 직접 결합으로 SQL Injection 위험 |
| `RETURNING` 및 404 | 대상 없는 UPDATE에 성공이라고 잘못 응답 |
| 트랜잭션 commit/rollback | 부분 실패 시 데이터 불일치 |
| Swagger + DB + GET Evidence | API 응답만 보고 저장 성공으로 오판 |

실무 추가 과제: 인증/인가, 수정 경쟁 상태(낙관적 잠금 등), DB CHECK 제약조건, 자동화된 pytest, 오류 응답의 OpenAPI 명시.

## 7. Definition of Done

- [x] PUT/PATCH 차이 설명 및 구현
- [x] PUT이 DB 행을 변경하고 조회 결과 일치 (3번 강의)
- [x] PATCH는 전달한 필드만 변경 (2번 강의)
- [x] 명시적 null 거부 422
- [x] 빈 PATCH 400
- [x] Parameterized UPDATE
- [x] Swagger Response = PostgreSQL Row = GET 재조회
- [x] Markdown 학습 기록 작성
- [ ] PATCH 없는 강의 ID 404 실제 실행 검증
- [ ] 잘못된 타입 422 실제 실행 검증
- [ ] PUT 필수 필드 누락 422 실제 실행 검증
- [ ] 이번 과제 소스코드 `courses.py`의 GitHub 별도 업로드 확인
- [ ] 첨부 캡처 ZIP 속 PNG를 GitHub 저장소에 업로드하고 문서에 이미지 연결

## 8. 스크린샷 파일 목록 (별도 첨부 ZIP)

```
chapter08-course-evidence-2026-11-02/
  01-create-table.png
  02-initial-courses.png
  03-get-before-put.png
  04-put-response.png
  05-get-after-put.png
  06-routes.png
  07-patch-response.png
  08-patch-db.png
  09-get-after-patch.png
  10-empty-patch-400.png
  11-explicit-null-422.png
```

## 9. 참고 자료

- 아토믹데브, [8강. PUT/PATCH + UPDATE — 전체 수정과 부분 수정](https://blog.naver.com/dev-dog/224457443890)
- 실습 대화에서 확보한 Swagger 및 DBeaver 캡처 (2026-11-02)

**원칙:** 수행하지 않은 테스트를 PASS 처리하지 않으며, 인증정보 및 비밀정보를 문서에 기록하지 않는다.
