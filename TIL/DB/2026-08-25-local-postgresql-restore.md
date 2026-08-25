# 2026-08-25 Local PostgreSQL Restore

## 정의: "DB를 로컬로 띄운다"는 무엇인가?

로컬 DB 구축은 단순히 DBeaver를 열거나 SQL 파일을 다운로드하는 작업이 아니다.

다음 세 가지가 모두 맞아야 한다.

1. PostgreSQL이 내 PC에서 실행 중이어야 한다.
2. Django가 그 PostgreSQL을 바라보도록 설정되어 있어야 한다.
3. 필요한 테이블과 데이터가 로컬 DB에 실제로 복원되어 있어야 한다.

전체 흐름은 다음과 같다.

```text
Django 코드
   ↓
DB 설정(settings.py / 환경변수)
   ↓
Local PostgreSQL
   ↑
SQL dump 복원
   ↑
psql 또는 DBeaver
```

## PostgreSQL, DBeaver, Django의 역할

- **PostgreSQL**: 실제 데이터를 저장하고 SQL을 처리하는 DBMS
- **DBeaver**: PostgreSQL 내부를 확인하고 SQL을 실행하는 GUI Client
- **psql**: PostgreSQL에 접속하고 SQL을 실행하는 CLI Client
- **Django**: 설정된 DB 접속 정보를 이용해 PostgreSQL을 사용하는 애플리케이션
- **SQL dump**: 테이블 구조와 데이터를 다시 만들 수 있는 SQL 명령 모음

즉 DBeaver와 psql은 DB 자체가 아니라 PostgreSQL에 접속하는 도구다.

## 왜 먼저 Django의 DB 설정을 확인했는가?

프로젝트를 전달받았다고 해서 실제 실행 DB가 자동으로 PostgreSQL이라고 단정할 수 없다.

Django는 `settings.py`의 `DATABASES` 설정과 환경변수에 따라 SQLite, PostgreSQL 등 서로 다른 DB를 사용할 수 있다.

그래서 프로젝트 전체에서 DB backend 관련 설정을 찾기 위해 다음 명령을 사용했다.

```cmd
findstr /S /I "django.db.backends" *.py
```

옵션 의미:

- `findstr`: Windows 파일 내부 문자열 검색
- `/S`: 하위 폴더까지 검색
- `/I`: 대소문자 구분 없이 검색
- `"django.db.backends"`: 찾을 문자열
- `*.py`: Python 파일만 검색

이 명령의 목적은 명령어 자체를 외우는 것이 아니라 **현재 프로젝트가 어느 DB 설정을 가지고 있는지 빠르게 추적하는 것**이었다.

중요한 점은 코드 안에 PostgreSQL과 SQLite 설정이 모두 있어도 실제 실행 시 어느 DB를 사용하는지는 최종 설정과 환경변수에 의해 결정된다는 것이다.

## SQL 파일을 받았다는 것과 DB가 복원됐다는 것은 다르다

SQL dump 파일은 단순한 데이터 파일이 아니라 실행해야 할 SQL 명령의 모음이다.

예를 들면 다음과 같은 내용이 포함될 수 있다.

```sql
CREATE TABLE ...;
INSERT INTO ...;
ALTER TABLE ...;
```

따라서:

```text
SQL 파일 다운로드
≠
DB 복원 완료
```

실제 복원은 다음 흐름으로 진행된다.

```text
SQL dump 보유
   ↓
PostgreSQL 접속
   ↓
복원 대상 DB 선택
   ↓
SQL 실행
   ↓
테이블 / 데이터 / 인덱스 / 제약조건 생성
   ↓
DBeaver에서 검증
```

## 핵심 명령: psql -f 로 SQL dump 복원

실제 계정명, DB명, 파일 경로는 공개 저장소에서 마스킹한다.

```bash
psql \
    -X -v ON_ERROR_STOP=1 \
    -h 127.0.0.1 -p 5432 \
    -U [LOCAL_DB_USER] -W \
    -d [LOCAL_CLONE_DB] \
    -f [SQL_DUMP_PATH]
```

이 명령의 목적은 **전달받은 SQL dump를 로컬 PostgreSQL의 별도 Clone DB에 실제로 실행해 운영 환경과 유사한 데이터 상태를 재현하는 것**이다.

### `psql`

PostgreSQL의 CLI Client다.

```text
DBeaver = GUI Client
psql    = CLI Client
```

### `-X`

사용자 개인의 psql 시작 설정을 읽지 않는다.

복원 작업에서 개인 환경 설정으로 실행 결과가 달라지는 것을 줄이기 위한 옵션이다.

### `-v ON_ERROR_STOP=1`

SQL 실행 중 오류가 발생하면 즉시 중단한다.

대량의 SQL 명령 중 중간 오류가 발생했는데 계속 실행되면 DB가 일부만 만들어진 상태가 될 수 있다.

```text
정상 실행
  ↓
오류 발생
  ↓
즉시 STOP
  ↓
실패 지점 확인
```

### `-h 127.0.0.1`

접속할 PostgreSQL 서버 주소를 지정한다.

`127.0.0.1`은 자기 자신의 컴퓨터이므로 외부 운영 DB가 아니라 로컬 PostgreSQL에 접속한다는 의미다.

### `-p 5432`

PostgreSQL 서버 포트를 지정한다.

`5432`는 PostgreSQL의 일반적인 기본 포트다.

### `-U [LOCAL_DB_USER]`

PostgreSQL에 접속할 DB 사용자를 지정한다.

실제 계정명은 공개 TIL에 기록하지 않는다.

### `-W`

비밀번호를 명령어에 직접 쓰지 않고 실행 시 입력받는다.

비밀번호를 명령문이나 Git 기록에 노출하지 않기 위한 방법이다.

### `-d [LOCAL_CLONE_DB]`

SQL dump를 복원할 대상 Database를 지정한다.

운영 DB가 아니라 별도로 만든 로컬 Clone DB를 사용해 안전하게 개발과 테스트를 진행한다.

### `-f [SQL_DUMP_PATH]`

실행할 SQL 파일 경로를 지정한다.

즉 `-f`가 실제로 **SQL 파일의 내용을 읽어 대상 DB에 실행하는 역할**을 한다.

## 왜 운영 DB가 아니라 Clone DB를 만드는가?

개발 중 운영 DB에 직접 연결하면 잘못된 SQL이나 코드로 실제 데이터를 변경할 위험이 있다.

따라서 일반적으로 환경을 분리한다.

```text
Local
  ↓ 개인 개발
Development / Test
  ↓ 팀 통합 테스트
Staging
  ↓ 운영 직전 검증
Production
  ↓ 실제 서비스
```

로컬 Clone DB의 목적은 운영 DB 자체를 건드리지 않으면서 비슷한 구조와 데이터를 사용해 기능을 테스트하는 것이다.

실제 운영 데이터를 로컬로 복제할 경우에는 개인정보와 민감 데이터가 비식별화/마스킹되어야 한다.

## DBeaver에서 무엇을 검증해야 하는가?

복원 명령이 끝났다고 바로 성공으로 판단하지 않는다.

DBeaver에서 다음을 확인한다.

- 대상 Database가 맞는가?
- 예상한 Schema가 존재하는가?
- Table이 생성됐는가?
- 데이터 Row가 들어왔는가?
- PK/FK 관계가 존재하는가?
- 인덱스와 제약조건이 필요한 수준으로 복원됐는가?

즉 실행 성공 메시지와 실제 DB 상태를 함께 검증해야 한다.

## Django와 로컬 DB를 최종 연결

Django의 DB 접속 설정과 실제 로컬 PostgreSQL 정보가 일치해야 한다.

```text
ENGINE   → PostgreSQL
HOST     → 로컬 DB 주소
PORT     → 로컬 PostgreSQL 포트
NAME     → 로컬 DB 이름
USER     → 로컬 DB 사용자
PASSWORD → 로컬 DB 비밀번호
```

비밀번호와 실제 운영 접속정보는 `.env` 등 환경변수로 분리하고 Git에 커밋하지 않는다.

공개 예시는 다음처럼 작성한다.

```env
DB_NAME=[LOCAL_DB_NAME]
DB_USER=[LOCAL_DB_USER]
DB_PASSWORD=********
DB_HOST=localhost
DB_PORT=[PORT]
```

## 오늘 가장 크게 이해한 것

처음에는 CMD 명령어를 외워야 한다고 생각했지만, 실제 개발에서는 먼저 **"지금 무엇을 확인하거나 바꾸려는가?"**를 정의해야 한다.

예를 들어:

```text
findstr → DB 설정 위치를 찾기 위해 사용
psql    → PostgreSQL에 접속하기 위해 사용
-d      → 대상 DB를 명확히 지정하기 위해 사용
-f      → SQL dump를 실제 DB에 실행하기 위해 사용
DBeaver → 복원된 DB 상태를 눈으로 검증하기 위해 사용
```

명령어는 목적을 달성하기 위한 수단이고, 중요한 것은 전체 시스템의 연결 구조를 이해하는 것이다.

## 전체 메커니즘

```text
[프로젝트 코드]
      │
      │ DB backend 추적
      ▼
[settings.py / .env]
      │
      │ 접속정보
      ▼
[Local PostgreSQL]
      ▲
      │ psql -f
      │
[SQL dump]
      │
      ▼
[DBeaver에서 검증]
      │
      ▼
[Django 실행 및 기능 테스트]
```

## 핵심 한 문장

**DB 로컬 구축은 SQL 파일을 여는 작업이 아니라 Django의 DB 설정, 로컬 PostgreSQL, SQL dump의 구조와 데이터를 하나의 연결된 실행 환경으로 맞추는 작업이며, `psql -f`는 SQL dump를 실제 로컬 DB 상태로 변환하는 복원 단계다.**
