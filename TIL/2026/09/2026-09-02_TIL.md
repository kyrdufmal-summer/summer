# TIL - 2026-09-02

## 오늘 한 일

오늘은 개인 지출관리 프로젝트를 기준으로 웹 애플리케이션의 전체 흐름을 정리하고,  
Flask / DB / HTTP / API / Webhook / 서버 인프라 개념을 서로 연결해서 이해했다.

단순히 코드를 한 줄씩 보는 것이 아니라  
**브라우저에서 입력한 데이터가 어디로 가고, 어떤 코드를 거쳐 DB에 저장되고, 다시 화면에 어떻게 나오는지**를 중심으로 정리했다.

---

## 1. 웹 서비스 전체 흐름 이해

웹 서비스를 볼 때 개별 코드보다 먼저 전체 흐름을 이해하는 것이 중요하다.

```text
브라우저
  ↓ HTTP 요청
Flask / Django
  ↓
Python 비즈니스 로직
  ↓
DB 연결 라이브러리
  ↓
PostgreSQL
  ↓
조회 결과
  ↓
HTML Template
  ↓
브라우저
```

현재 개인 지출관리 프로젝트에서는 다음과 같이 연결된다.

```text
브라우저
→ Flask(app.py)
→ psycopg2
→ PostgreSQL
→ Jinja HTML
→ 브라우저
```

### 배운 점

Flask는 서버 컴퓨터 그 자체가 아니라  
Python으로 웹 애플리케이션을 만들기 위한 **웹 프레임워크**이다.

Java에서 Spring Boot를 사용하는 것과 비슷한 위치라고 이해하면 된다.

---

## 2. 브라우저 → 서버 → Flask 흐름

브라우저에서 주소를 입력하면 HTTP 요청이 발생한다.

예:

```text
http://127.0.0.1:5000/
```

여기서

- `127.0.0.1` : 내 컴퓨터(Localhost)
- `5000` : Flask 애플리케이션이 사용하는 Port
- `/` : Flask Route

Flask에서 다음과 같이 작성하면

```python
@app.route("/")
def dashboard():
    ...
```

브라우저에서 `/`로 요청했을 때 `dashboard()` 함수가 실행된다.

---

## 3. GET과 POST 차이

웹에서 데이터를 전달할 때 GET과 POST의 역할이 다르다.

### GET

데이터를 조회할 때 주로 사용한다.

예:

```text
/expense_list.html?category=식비
```

HTML:

```html
<select name="category">
```

Flask:

```python
request.args.get("category")
```

흐름은 다음과 같다.

```text
HTML name
→ URL Query String
→ request.args
→ Python
```

### POST

사용자가 입력한 데이터를 서버에 전달해서 저장할 때 주로 사용한다.

HTML:

```html
<form method="POST">
```

Flask:

```python
request.form.get("amount")
```

흐름은 다음과 같다.

```text
사용자 입력
→ POST
→ request.form
→ Python
→ SQL INSERT
→ PostgreSQL
```

---

## 4. 개인 지출관리 프로젝트 구조

현재 프로젝트의 기본 구조는 다음과 같다.

```text
personal-expense-manager/

├─ app.py
├─ db_test.py
├─ templates/
│  ├─ dashboard.html
│  ├─ expense_add.html
│  └─ expense_list.html
│
└─ static/
   └─ style.css
```

### app.py 역할

`app.py`는 단순한 함수 파일이 아니라 웹 애플리케이션의 중심 파일이다.

주요 역할:

- Flask 실행
- URL Routing
- 사용자 요청 처리
- DB 조회
- DB 저장
- HTML Template에 데이터 전달

즉, 현재 프로젝트에서는 Controller 역할과 비즈니스 로직이 함께 들어가는 중심 파일이라고 볼 수 있다.

---

## 5. 지출관리 함수의 역할 정리

프로젝트에서 사용하는 주요 함수의 역할을 다시 정리했다.

```python
# 지출 등록
add_expense()

# 지출 목록 조회
show_expenses()

# 전체 합계 계산
calculate_total()

# 카테고리별 합계 계산
calculate_by_category()

# DB 지출 저장
save_expenses()

# DB 지출 조회
load_expenses()
```

웹 프로젝트에서는 이러한 Python 함수가 Flask Route와 연결된다.

예:

```text
지출 등록 화면
→ POST
→ add_expense()
→ save_expenses()
→ PostgreSQL
```

---

## 6. PostgreSQL INSERT와 commit 이해

지출을 저장할 때 SQL은 다음과 같은 구조를 가진다.

```sql
INSERT INTO expenses (
    date,
    category,
    description,
    amount
)
VALUES (%s, %s, %s, %s)
```

INSERT / UPDATE / DELETE 이후에는

```python
conn.commit()
```

을 실행해야 실제 DB에 반영된다.

전체 흐름:

```text
HTML 입력
→ Flask POST
→ request.form
→ SQL INSERT
→ conn.commit()
→ PostgreSQL 저장
```

### 배운 점

SQL 문을 실행한 것과 DB에 실제 반영된 것은 다를 수 있다.  
트랜잭션을 확정하는 `commit()`까지 이해해야 저장 흐름을 정확하게 볼 수 있다.

---

## 7. DB 데이터와 드롭다운 불일치 문제

DB에는 `놀이비` 데이터가 존재하지만 웹 화면의 드롭다운에 나오지 않는 문제가 있었다.

원인은 DB 자체보다는 HTML의 `<select>` 옵션을 직접 작성한 **하드코딩 방식**일 가능성이 컸다.

예:

```html
<option value="식비">식비</option>
<option value="교통">교통</option>
<option value="카페">카페</option>
```

DB에 새로운 카테고리를 추가해도 HTML에 옵션을 추가하지 않으면 자동으로 나타나지 않는다.

### 개선 방향

DB에서 카테고리를 직접 조회한다.

```sql
SELECT DISTINCT category
FROM expenses
ORDER BY category;
```

Flask에서 조회한 결과를 Template에 전달하고, HTML에서는 반복문으로 출력하면 된다.

```html
{% for category in categories %}
<option value="{{ category }}">
    {{ category }}
</option>
{% endfor %}
```

### 배운 점

DB에 이미 존재하는 데이터를 화면에서도 사용해야 한다면  
HTML에 같은 값을 다시 하드코딩하기보다 **DB를 단일 기준(Source of Truth)**으로 사용하는 것이 유지보수에 유리하다.

---

## 8. 지출관리 Dashboard의 비즈니스 지표

단순히 그래프를 넣는 것보다 먼저  
가계부에서 어떤 정보를 확인하고 싶은지 정한 뒤 그래프를 선택해야 한다.

현재 프로젝트에서 유용한 지표는 다음과 같다.

### 기본 KPI

- 전체 지출 금액
- 지출 건수
- 가장 큰 지출
- 카테고리별 지출 합계

### 추가하면 좋은 지표

- 일별 지출 추이
- 월별 지출 추이
- 카테고리별 지출 비중
- 가장 많이 지출한 카테고리
- 평균 지출 금액
- 최근 지출 내역

---

## 9. Matplotlib 활용 방향

Matplotlib를 사용하면 Flask Dashboard용 그래프를 만들 수 있다.

가계부에서는 특히 다음 그래프가 적절하다.

### 막대그래프

카테고리별 지출 비교에 적합하다.

### 원형그래프

전체 지출 중 카테고리별 비율을 확인할 때 사용할 수 있다.

### 선그래프

날짜별 또는 월별 지출 추이를 확인할 때 적합하다.

### 배운 점

그래프를 먼저 선택하는 것이 아니라 다음 순서로 설계하는 것이 중요하다.

```text
Business Question
→ 필요한 데이터
→ 집계
→ 적합한 그래프
```

---

## 10. IP와 Port 이해

### IP

컴퓨터 또는 서버를 구별하는 주소이다.

```text
127.0.0.1
```

은 자신의 컴퓨터를 의미한다.

### Port

한 컴퓨터 안에서 어떤 프로그램으로 요청을 보낼지를 구분한다.

예:

```text
127.0.0.1:5000
```

- IP → 어떤 컴퓨터인가
- Port → 그 컴퓨터의 어떤 프로그램인가

---

## 11. API와 Webhook 이해

### API

프로그램과 프로그램 사이에 데이터를 주고받는 약속이다.

예:

```text
브라우저
→ Flask API
→ DB
```

또는

```text
우리 서버
→ 외부 서비스 API
```

### Webhook

일반 API는 내가 상대방에게 요청하는 흐름이 많다.

```text
내 서버
→ 상대방 API
```

Webhook은 특정 이벤트가 발생하면 상대방이 미리 등록된 URL로 알려주는 방식이다.

```text
이벤트 발생
→ 외부 서비스
→ 우리 서버 Webhook URL 호출
```

Slack Webhook도 이 개념으로 이해할 수 있다.

---

## 12. 실제 서비스의 서버 구조

로컬 Flask만 실행할 때보다 실제 서비스 환경에서는 구성 요소가 더 추가된다.

```text
사용자
↓
Nginx / Caddy
↓
Gunicorn
↓
Django / Flask
↓
PostgreSQL
```

### Nginx / Caddy

외부 요청을 가장 먼저 받는 Web Server이다.

### Gunicorn

Python 웹 애플리케이션을 실제 서버 환경에서 실행하는 WSGI Server이다.

### Django / Flask

웹 애플리케이션의 기능과 비즈니스 로직을 담당한다.

---

## 13. Docker와 Linux Server 기본 개념

Docker는 애플리케이션 실행 환경을 Container로 묶어 관리하는 기술이다.

예를 들어

- Python 버전
- 설치 패키지
- Flask / Django
- 실행 설정

등을 동일하게 유지할 수 있다.

### 배운 점

개발 환경과 서버 환경의 차이 때문에 발생하는

> 내 PC에서는 되는데 서버에서는 안 된다

는 문제를 줄이는 데 Docker가 도움이 된다.

---

## 14. 프로젝트 / Git 운영 흐름

AX2 통합 프로젝트에서는 단순히 코드를 작성하는 것뿐 아니라  
GitHub Issue, Branch, PR, Deliverable을 연결해서 관리하는 것이 중요하다.

전체 흐름은 다음과 같다.

```text
Issue
↓
작업
↓
Branch
↓
Commit
↓
PR
↓
Review
↓
Merge
↓
Deliverable
↓
Issue GREEN / Close
```

전날 Daily Issue가 YELLOW 상태라면 다음 날 새 Issue만 GREEN 처리하는 것이 아니라  
전날 미완료 작업도 이어서 완료하고 함께 GREEN 상태로 관리해야 한다.

---

## 15. 보안 관련 주의사항

`.env`, API Token, Webhook URL 등의 값은  
GitHub Issue, README, TIL 같은 문서에 그대로 기록하면 안 된다.

예:

```env
SLACK_WEBHOOK_URL=***
SLACK_BOT_TOKEN=***
DB_PASSWORD=***
API_KEY=***
```

GitHub Repository에 올릴 때도 `.env`는 `.gitignore`로 관리해야 한다.

### 배운 점

기능이 정상 동작하는 것만큼  
**인증정보와 비밀값을 소스와 문서에서 분리하는 것**도 개발의 기본이다.

---

## 오늘 가장 중요하게 배운 점

오늘 가장 크게 이해한 것은 웹 애플리케이션을 볼 때  
코드 한 줄씩 따로 보는 것보다 전체 데이터 흐름으로 연결해서 보는 것이 중요하다는 점이다.

```text
브라우저
→ HTTP
→ Flask / Django
→ Python
→ DB
→ Python
→ Template
→ 브라우저
```

그리고 실제 서비스 환경에서는 그 앞뒤에

```text
Nginx / Caddy
→ Gunicorn
→ Flask / Django
→ PostgreSQL
```

같은 인프라 요소들이 추가된다.

---

## 오늘의 한 줄 정리

> **웹 개발은 코드를 외우는 것이 아니라, 데이터가 어디에서 와서 어디를 거쳐 저장되고 다시 어디에 표시되는지 흐름으로 이해하는 것이 핵심이다.**
