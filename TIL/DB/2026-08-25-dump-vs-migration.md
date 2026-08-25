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

Dump 파일은 **현재 DB를 다른 곳에서 다시 재현할 수 있도록 뽑아둔 결과물**이다.

이번 프로젝트처럼 이해하면 가장 쉽다.

```text
V1에서 사용하던 DB
   ↓
dump 파일로 추출
   ↓
로컬 PostgreSQL에 복원
   ↓
V1과 비슷한 DB 복제본 생성
   ↓
V2 개발에서 사용
```

즉 이번 상황에서 dump는 거의 **"V1 DB를 데이터까지 포함해 복사해서 V2에서 쓸 수 있도록 만드는 재료"**라고 이해하면 된다.

다만 DB에는 실제 데이터만 있는 것이 아니다.

예를 들어 다음이 함께 존재한다.

```text
student 테이블
team 테이블
evaluation 테이블

+ 각 테이블의 컬럼 구조
+ PK / FK
+ 인덱스
+ 제약조건
+ 실제 학생/팀/평가 데이터
```

따라서 dump는 단순히 학생 이름이나 평가점수 같은 **값만 복사하는 것**이 아니라, 필요에 따라 그 값을 담을 **DB의 틀까지 함께 옮길 수 있다.**

### 엑셀로 비유하면

단순 데이터 복사는:

```text
김철수 / 90점
이영희 / 85점
```

처럼 셀 값만 복사하는 느낌이다.

반면 DB dump는 필요에 따라:

```text
시트 이름
열 구조
관계와 규칙
실제 셀 데이터
```

까지 같이 복사해서 **원래 파일과 비슷한 상태를 다시 만드는 것**에 가깝다.

### 어디에 쓰는가?

- DB 백업
- 운영 DB 구조와 데이터를 로컬에 재현
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

## 3. 왜 Dump 방식이 여러 가지인가?

### 먼저 정의

Dump 방식이 여러 개인 이유는 **DB를 내보내는 목적이 서로 다르기 때문**이다.

항상 모든 구조와 모든 데이터를 통째로 복사해야 하는 것은 아니다.

예를 들어 같은 DB라도 상황에 따라 필요한 범위가 달라진다.

### 1) 구조만 필요한 경우

신규 개발자에게 실제 사용자 개인정보는 주고 싶지 않지만 테이블 구조는 동일하게 만들고 싶을 수 있다.

```text
기존 DB
   ↓
테이블 구조만 dump
   ↓
빈 DB 생성
   ↓
더미데이터 별도 입력
```

이 경우 실제 데이터는 빼고 Schema만 가져간다.

### 2) 데이터만 필요한 경우

이미 테이블 구조는 동일하게 만들어져 있고, 특정 데이터만 옮기고 싶은 경우다.

```text
기존 DB 데이터
   ↓
데이터만 추출
   ↓
이미 존재하는 테이블에 입력
```

### 3) 구조 + 데이터 둘 다 필요한 경우

기존 환경과 최대한 비슷한 상태를 재현하고 싶을 때 사용한다.

이번 프로젝트의 로컬 Clone DB 목적이 여기에 가깝다.

```text
V1 DB
   ↓
구조 + 데이터 dump
   ↓
Local Clone DB
   ↓
V2에서 기능 확인
```

### 4) 특정 테이블만 필요한 경우

DB 전체가 매우 크거나 특정 기능만 테스트하고 싶은 경우 전체 DB를 옮길 필요가 없다.

```text
전체 DB
├─ users
├─ orders
├─ evaluation  ← 이것만 필요
└─ logs
```

필요한 테이블만 선택해서 dump할 수 있다.

### 결국 왜 여러 방식이 필요한가?

```text
백업 목적
개발 목적
테스트 목적
개인정보 보호
용량 절감
일부 기능만 재현
```

등 목적이 모두 다르기 때문이다.

즉 **dump 방식이 복잡해서 여러 개인 것이 아니라, "무엇을 얼마나 복사할 것인가"를 선택할 수 있도록 여러 옵션이 있는 것**이다.

---

## 4. 개발자가 "DB 백업해놔"라고 하면 무슨 뜻인가?

### 정의

**백업(Backup)**은 현재 상태가 나중에 망가지거나 사라져도 다시 되돌릴 수 있도록 복사본을 따로 만들어 보관하는 것이다.

DB 기준으로는:

```text
현재 DB
   ↓
백업 파일 생성
   ↓
안전한 곳에 보관
```

이다.

### 왜 백업을 하는가?

개발 과정에서는 다음과 같은 일이 생길 수 있다.

- 데이터를 실수로 삭제
- 테이블 구조를 잘못 변경
- migration 실패
- 서버 장애
- 배포 후 데이터 문제 발생
- 잘못된 SQL 실행

이때 백업이 있다면:

```text
문제 발생
   ↓
백업 파일 사용
   ↓
DB 복원
   ↓
이전 상태로 되돌림
```

할 수 있다.

그래서 개발자가:

> "DB 수정하기 전에 백업해놔."

라고 말하면 거의 다음 뜻이다.

> **"지금 DB를 망쳐도 원래 상태로 복구할 수 있도록 dump 같은 복사본을 먼저 만들어 둬."**

### Backup과 Restore 차이

이 둘도 구분해야 한다.

```text
Backup
= 지금 상태를 복사해서 저장해 두기

Restore
= 저장해 둔 복사본으로 DB를 다시 되살리기
```

예를 들어:

```text
V1 운영 DB
   ↓ pg_dump
백업 dump 파일
   ↓ psql / pg_restore
Local Clone DB
```

여기서:

- dump 파일을 만든 것 = **Backup**
- 그 dump를 로컬 DB에 넣은 것 = **Restore**

라고 볼 수 있다.

---

## 5. Django Migration이란?

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

## 6. `python manage.py migrate`는 왜 실행할까?

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

## 7. 왜 VS Code 터미널에서 `migrate`를 실행할까?

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

## 8. `makemigrations`와 `migrate` 차이

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

## 9. Dump와 Migration은 왜 둘 다 필요할까?

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

## 10. Dump를 복원했는데도 `migrate`가 필요한 이유

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

## 11. 실제로 겪은 예: `axes_accessattempt` 테이블 오류

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

## 12. 개발자들이 "마이그레이션"이라고 말할 때 의미

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

## 13. 지금 프로젝트 상황에 대입하면

오늘 작업을 분리해서 보면 다음과 같다.

### 1) SQL Dump 복원

```text
V1 DB
   ↓
SQL dump
   ↓
psql -f
   ↓
Local PostgreSQL Clone DB
   ↓
V2 개발에서 사용
```

목적:

> V1에서 사용하던 DB 상태를 운영 DB 자체를 건드리지 않고 로컬에 재현해 V2 개발에 활용

### 2) Django Migration 적용

```text
Django migration 파일
   ↓
python manage.py migrate
   ↓
현재 V2 코드가 요구하는 DB 구조까지 반영
```

목적:

> 현재 애플리케이션과 DB 스키마 버전을 맞춤

즉 이번 프로젝트 흐름은 다음과 같이 이해하면 된다.

```text
V1 DB
→ dump로 복제 재료 생성
→ 로컬 DB에 Restore
→ V2가 복제 DB 사용
→ 필요한 최신 변경은 migrate로 추가 반영
```

---

## 14. 전체 메커니즘

```text
[V1 운영 또는 기준 DB]
       │
       │ Backup / Dump 생성
       ▼
[SQL Dump]
       │
       │ Restore: psql -f / pg_restore
       ▼
[Local PostgreSQL Clone]
       │
       │ 현재 V2 코드와 구조 차이 존재 가능
       ▼
[Django Migration 파일]
       │
       │ python manage.py migrate
       ▼
[V2 코드와 맞는 DB 구조]
       │
       ▼
[Django 서버 실행 및 개발]
```

---

## 15. 핵심 한 문장

```text
dump      = DB를 복제하거나 복원하기 위해 뽑아둔 결과물
backup    = 그 dump 같은 복사본을 안전하게 보관하는 행위
restore   = 백업된 dump를 다시 DB로 되살리는 행위
migration = DB 구조 변화의 이력
migrate   = 그 변화를 실제 DB에 적용하는 실행
```

그리고 이번 프로젝트에서는 **V1 DB를 dump로 추출해 로컬 Clone DB에 복원하고, 그 DB를 V2 개발에 사용한 뒤 필요한 최신 스키마 변경은 Django migrate로 반영하는 흐름**으로 이해하면 된다.
