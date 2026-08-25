# Dump와 Migration의 차이 — Django에서 `migrate`를 왜 실행할까?

## 1. 먼저 정의부터

DB를 다루다 보면 `dump`, `migration`, `migrate`라는 말을 자주 듣는다.

처음에는 셋 다 "DB를 옮기거나 만드는 작업"처럼 들리지만 실제로 역할이 다르다.

가장 짧게 정리하면 다음과 같다.

```text
dump      = DB를 다시 만들 수 있도록 뽑아둔 백업/복원용 결과물
migration = DB 구조가 어떻게 바뀌어야 하는지 기록한 변경 이력
migrate   = 그 변경 이력을 실제 DB에 적용하는 실행
```

이 세 가지를 구분하면 Django와 PostgreSQL을 함께 쓸 때 흐름이 훨씬 잘 보인다.

---

## 2. Dump 파일이란?

### 정의

Dump 파일은 **현재 DB의 구조와 데이터를 다른 DB에 다시 재현할 수 있도록 추출한 결과물**이다.

예를 들어 PostgreSQL 안에 다음 테이블이 있다고 하자.

```text
users
orders
products
```

그리고 각 테이블 안에 데이터가 들어 있다면, dump를 만들 때 다음과 같은 정보가 함께 들어갈 수 있다.

```sql
CREATE TABLE users (...);
INSERT INTO users (...);
ALTER TABLE ...;
CREATE INDEX ...;
```

즉 dump는 단순한 데이터 파일이 아니라,

> **"이 DB를 다시 만들기 위한 구조 + 데이터 + 부가 객체의 묶음"**

이라고 이해하면 된다.

### 어디에 쓰는가?

- DB 백업
- 운영 DB 구조를 로컬에 재현
- 다른 서버로 DB 이전
- 장애 발생 시 복원
- 테스트 환경 구성

전체 흐름은 다음과 같다.

```text
기존 DB
   ↓
Dump 생성
   ↓
Dump 파일
   ↓
다른 PostgreSQL에 Restore
   ↓
복제된 DB
```

---

## 3. Django Migration이란?

### 정의

Django에서 migration은 **`models.py`의 변경 내용을 실제 DB 구조에 반영하기 위한 변경 이력 파일**이다.

예를 들어 Django 모델이 처음에는 이렇게 있었다고 하자.

```python
class Student(models.Model):
    name = models.CharField(max_length=100)
```

나중에 전화번호 컬럼을 추가한다.

```python
class Student(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
```

코드만 바꿨다고 PostgreSQL의 실제 테이블에 `phone` 컬럼이 자동으로 생기지는 않는다.

Django는 먼저 변경 이력을 만든다.

```bash
python manage.py makemigrations
```

그러면 Django가 대략 이런 의미의 migration 파일을 만든다.

```text
Student 모델에 phone 필드를 추가해야 한다.
```

즉 `makemigrations`는:

> **"모델이 이렇게 바뀌었으니 DB를 이렇게 바꿔야 한다"는 설계서/변경 이력을 만드는 과정**

이다.

---

## 4. `python manage.py migrate`는 왜 실행할까?

### 정의

`migrate`는 **Django가 만들어 둔 migration 파일을 실제 DB에 적용하는 명령**이다.

```bash
python manage.py migrate
```

흐름은 다음과 같다.

```text
models.py 수정
   ↓
makemigrations
   ↓
migration 파일 생성
   ↓
migrate
   ↓
실제 PostgreSQL 테이블 변경
```

즉 `migrate`는 단순히 Django를 실행하는 명령이 아니다.

> **현재 Django 코드가 기대하는 DB 구조와 실제 DB 구조를 맞추는 작업**

이다.

---

## 5. 왜 VS Code 터미널에서 `migrate`를 실행할까?

중요한 점은 **VS Code라서 migrate를 하는 것이 아니다.**

VS Code 터미널은 단순히 명령어를 입력하는 공간이다.

다음 어디에서 실행해도 된다.

```text
CMD
PowerShell
VS Code Terminal
PyCharm Terminal
```

중요한 조건은 다음이다.

- Django 프로젝트 폴더에 있어야 한다.
- `manage.py`가 있는 위치여야 한다.
- 올바른 Python 가상환경이 활성화되어 있어야 한다.
- Django가 연결할 DB 설정이 올바르게 잡혀 있어야 한다.

즉 VS Code 터미널에서 실행하는 이유는 **개발 중인 프로젝트와 같은 환경에서 바로 명령을 실행하기 편하기 때문**이다.

---

## 6. `makemigrations`와 `migrate` 차이

이 둘은 자주 헷갈린다.

### `makemigrations`

```bash
python manage.py makemigrations
```

역할:

```text
모델 변경 감지
   ↓
DB 변경 설계서 생성
```

즉 실제 DB를 바로 바꾸는 것이 아니라 **변경 이력을 만든다.**

### `migrate`

```bash
python manage.py migrate
```

역할:

```text
migration 파일 읽기
   ↓
실제 DB에 적용
```

즉 이미 만들어진 변경 이력을 **실제 PostgreSQL에 실행한다.**

한 줄로 정리하면:

```text
makemigrations = 변경사항 기록
migrate        = 변경사항 적용
```

---

## 7. Dump와 Migration은 왜 둘 다 필요할까?

둘의 목적이 다르기 때문이다.

| 구분 | Dump | Django Migration |
|---|---|---|
| 핵심 목적 | DB 백업/복원/복제 | DB 구조 변경 이력 관리 |
| 데이터 포함 | 포함 가능 | 일반적으로 스키마 변경 중심 |
| 생성 주체 | PostgreSQL 도구 등 | Django |
| 대표 명령 | `pg_dump` | `python manage.py makemigrations` |
| 적용 방식 | `psql -f`, `pg_restore` | `python manage.py migrate` |

쉽게 표현하면:

```text
Dump
= DB의 한 시점을 복사해 두는 것
```

```text
Migration
= DB 구조가 시간에 따라 어떻게 변했는지 기록하는 것
```

---

## 8. Dump를 복원했는데도 `migrate`가 필요한 이유

이 부분이 실제 개발에서 중요하다.

예를 들어 어떤 시점의 운영 DB dump를 로컬에 복원했다고 하자.

```text
운영 DB dump
   ↓
로컬 PostgreSQL 복원
```

그런데 현재 Git 저장소의 Django 코드는 dump가 만들어진 시점보다 더 최신일 수 있다.

예:

```text
Dump 시점
→ users 테이블까지만 존재

현재 Django 코드
→ users + axes_accessattempt 테이블 필요
```

그러면 dump를 복원해도 현재 코드가 요구하는 테이블이 부족할 수 있다.

그래서 다음이 필요하다.

```bash
python manage.py migrate
```

즉:

```text
Dump Restore
= 과거 특정 시점의 DB 상태 재현

migrate
= 현재 Django 코드가 요구하는 최신 DB 구조까지 업데이트
```

이라고 이해하면 된다.

---

## 9. 실제로 겪은 예: `axes_accessattempt` 테이블 오류

Django 서버를 실행했을 때 다음과 같은 오류가 발생할 수 있다.

```text
no such table: axes_accessattempt
```

이 의미는:

```text
Django 코드
→ axes 관련 테이블이 필요함

현재 DB
→ 해당 테이블이 없음
```

상태다.

이럴 때 `django-axes` 패키지가 정상 설치되어 있고 migration 파일도 존재한다면 다음 명령으로 필요한 DB 구조를 적용할 수 있다.

```bash
python manage.py migrate
```

즉 패키지가 설치되어 있는 것과 DB에 해당 테이블이 실제로 만들어져 있는 것은 별개의 문제다.

---

## 10. 개발자들이 "마이그레이션"이라고 말할 때 의미

`migration`은 문맥에 따라 범위가 달라진다.

### Django 개발 문맥

개발자가:

> "마이그레이션 돌려주세요."

라고 말하면 보통 다음을 의미한다.

```bash
python manage.py migrate
```

즉 **DB 스키마 변경 이력을 실제 DB에 적용하라**는 뜻이다.

예:

```text
users 테이블에 phone 컬럼 추가
   ↓
makemigrations
   ↓
migrate
```

### 프로젝트 전체 문맥

반면 다음처럼 말할 수도 있다.

> "기존 시스템을 신규 시스템으로 마이그레이션한다."

이때는 훨씬 넓은 의미다.

```text
기존 시스템
   ↓
데이터 추출
   ↓
형식 변환
   ↓
신규 시스템
   ↓
검증 및 전환
```

이 경우에는 다음과 같은 표현을 사용한다.

- DB Migration
- Data Migration
- Server Migration
- Cloud Migration
- Application Migration

즉 여기서 migration은:

> **기존 환경의 데이터·구조·시스템을 새로운 환경으로 옮기는 전체 과정**

을 뜻한다.

---

## 11. 지금 프로젝트 상황에 대입하면

오늘 작업을 분리해서 보면 다음과 같다.

### 1) SQL Dump 복원

```text
SQL dump
   ↓
psql -f
   ↓
Local PostgreSQL Clone DB
```

목적:

> 운영과 유사한 DB 상태를 로컬에 재현

### 2) Django Migration 적용

```text
Django migration 파일
   ↓
python manage.py migrate
   ↓
현재 코드가 요구하는 DB 구조까지 반영
```

목적:

> 현재 애플리케이션과 DB 스키마 버전을 맞춤

둘은 비슷해 보여도 역할이 다르다.

---

## 12. 전체 메커니즘

```text
[운영 또는 기준 DB]
       │
       │ dump 생성
       ▼
[SQL Dump]
       │
       │ psql -f / pg_restore
       ▼
[Local PostgreSQL]
       │
       │ 현재 코드와 구조 차이 존재 가능
       ▼
[Django Migration 파일]
       │
       │ python manage.py migrate
       ▼
[현재 Django 코드와 맞는 DB 구조]
       │
       ▼
[Django 서버 실행]
```

---

## 13. 핵심 한 문장

```text
dump      = DB의 복사본 또는 복원 재료
migration = DB 구조 변화의 이력
migrate   = 그 변화를 실제 DB에 적용하는 실행
```

그리고 개발 프로젝트에서의 **마이그레이션**은 좁게는 DB 스키마 변경 적용을 뜻하고, 넓게는 기존 시스템의 데이터·구조·서비스를 새로운 환경으로 이전하는 전체 작업을 뜻한다.
