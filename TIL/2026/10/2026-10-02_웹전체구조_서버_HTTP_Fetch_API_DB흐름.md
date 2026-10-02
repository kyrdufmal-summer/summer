# 2026-10-02 TIL — 웹 전체 구조와 서버 역할, HTTP·Fetch·API·DB 흐름

## 오늘의 핵심

오늘은 Frontend Basic 실습을 통해 화면 코드만 보는 것이 아니라 **브라우저의 요청이 어떤 서버를 거쳐 데이터베이스까지 갔다가 다시 화면으로 돌아오는지**를 전체 흐름으로 이해했다.

핵심 구조는 두 가지로 정리할 수 있다.

~~~text
[현재 WAMP/PHP 실습]

Browser
  ↓ HTTP Request
Apache Web Server
  ↓
PHP
  ↓ SQL
MySQL
  ↓
PHP
  ↓ HTML Response
Browser
~~~

~~~text
[현대적인 API 기반 구조 예]

React + TypeScript
  ↓ HTTP / JSON
FastAPI
  ↓ SQL
Database
  ↑
JSON Response
  ↑
JavaScript
  ↓
DOM
~~~

오늘의 가장 중요한 결론은 **브라우저, Web Server, Backend, Database가 각각 다른 역할을 맡고 있으며 오류가 나면 이 계층을 순서대로 확인해야 한다**는 것이다.

---

# 1. 웹 서비스를 한 문장으로 이해하기

웹 서비스는 사용자가 브라우저에서 요청을 보내면 서버가 요청을 처리하고 필요한 경우 DB에서 데이터를 가져와 결과를 다시 브라우저에 보내는 구조다.

~~~text
사용자 클릭
↓
Browser
↓
HTTP Request
↓
Server
↓
Application
↓
Database
↓
Application
↓
HTTP Response
↓
Browser
~~~

브라우저가 MySQL이나 PostgreSQL에 직접 접속하는 구조가 아니라 **Backend가 DB와 통신하는 중간 역할**을 한다.

---

# 2. Frontend / Backend / Web Server / DB 역할

## Frontend

사용자가 직접 보는 화면이다.

예:
- HTML
- CSS
- JavaScript
- React
- TypeScript

담당:
- 버튼
- 입력창
- 표
- 화면 렌더링
- 사용자 이벤트
- API 요청

## Web Server

브라우저의 HTTP 요청을 가장 먼저 받는 서버다.

예:
- Apache
- Nginx

담당:
- HTML/CSS/JS 같은 정적 파일 전달
- HTTP 요청 수신
- HTTPS 종료
- Reverse Proxy
- Backend로 요청 전달

## Backend / Application Server

업무 로직을 처리한다.

예:
- PHP
- FastAPI
- Django
- Spring

담당:
- 회원가입
- 로그인
- 주문
- 수강신청
- 검색
- DB 조회/수정
- JSON 또는 HTML 응답 생성

## Database

서비스의 데이터를 저장한다.

예:
- MySQL
- PostgreSQL

담당:
- 학생
- 강의
- 회원
- 주문
- 결제
- 관계 데이터

---

# 3. 현재 WAMP 실습 구조

오늘 실습 환경은 Windows에서 WAMP를 사용한다.

~~~text
WAMP
= Windows
+ Apache
+ MySQL
+ PHP
~~~

흐름은 다음과 같다.

~~~text
Browser
↓
Apache
↓
PHP
↓
MySQL
↓
PHP
↓
HTML
↓
Browser
~~~

예를 들어 Students 버튼을 누르면:

~~~text
1. Browser가 students.php 요청
2. Apache가 요청을 받음
3. PHP 코드 실행
4. PHP가 MySQL에 SELECT 실행
5. MySQL이 결과 반환
6. PHP가 결과를 HTML table로 변환
7. Apache가 HTML 응답
8. Browser가 화면에 표시
~~~

여기서 핵심은 **PHP가 Browser와 DB 사이를 연결한다**는 점이다.

---

# 4. 정적 웹과 동적 웹

## 정적 웹

미리 만들어진 파일을 그대로 전달한다.

~~~text
Browser
↓ GET /index.html
Apache
↓
index.html
~~~

예:
- 소개 페이지
- 단순 HTML 문서
- 이미지
- CSS
- JavaScript 파일

## 동적 웹

사용자의 요청이나 DB 데이터에 따라 결과가 달라진다.

~~~text
Browser
↓
students.php
↓
PHP
↓
SELECT ...
↓
MySQL
↓
조회 결과
↓
PHP가 HTML 생성
↓
Browser
~~~

학생이 추가되면 같은 students.php를 열어도 화면 내용이 달라진다.

---

# 5. DevTools에서 실제 요청 확인

F12 개발자도구는 브라우저에서 웹 서비스 내부 흐름을 확인하는 중요한 도구다.

## Elements

현재 브라우저가 렌더링한 DOM 구조를 확인한다.

예:

~~~html
<h1>Frontend 학습을 시작합니다.</h1>
~~~

## Network

브라우저가 서버와 주고받은 HTTP 요청을 확인한다.

페이지 새로고침 후 index.html 요청을 선택하면 다음을 볼 수 있다.

~~~text
Request URL
Request Method: GET
Status Code
~~~

이것은 단순 화면 확인이 아니라:

~~~text
Browser
→ Web Server에 GET 요청
→ Web Server가 Response 반환
~~~

이라는 실제 통신을 눈으로 확인하는 것이다.

---

# 6. GET과 POST의 핵심 차이

## GET

주로 데이터를 **조회**할 때 사용한다.

예:

~~~text
학생 목록 보기
상품 검색
게시글 조회
~~~

개념:

~~~text
Browser
→ GET /students
→ Server
→ 학생 목록 반환
~~~

## POST

주로 새로운 데이터를 서버에 **전달하거나 생성**할 때 사용한다.

예:

~~~text
학생 등록
회원가입
주문 생성
~~~

개념:

~~~text
Browser
→ POST /students
   name=***
   email=***
→ Server
→ DB INSERT
~~~

실무에서는 HTTP Method의 의미를 API 설계 기준에 맞춰 사용한다.

---

# 7. Fetch는 무엇을 하는가

fetch는 JavaScript가 브라우저에서 서버/API에 HTTP 요청을 보내는 기능이다.

예를 들어 상품 목록 API가 있다고 하면:

~~~text
JavaScript
↓ fetch()
API Server
↓
JSON
↓
JavaScript
~~~

즉 fetch 자체가 데이터를 만드는 것이 아니라 **서버에 요청하고 응답을 받아오는 역할**을 한다.

---

# 8. API → JSON → JavaScript → DOM 흐름

오늘 중요하게 본 흐름이다.

예:

~~~text
사용자
↓
상품조회 버튼 클릭
↓
JavaScript
↓
fetch('/api/products')
↓
API Server
↓
Database 조회
↓
JSON Response
↓
JavaScript가 JSON 해석
↓
DOM 수정
↓
Browser 화면 변경
~~~

예시 JSON:

~~~json
[
  {
    "id": 1,
    "name": "운동화",
    "price": 59000
  }
]
~~~

JavaScript는 이 데이터를 받아 화면의 HTML 요소를 생성하거나 변경한다.

즉:

> API는 데이터를 제공하고, JSON은 전달 형식이며, JavaScript는 데이터를 처리하고, DOM은 최종 화면을 바꾼다.

---

# 9. React + FastAPI 구조로 확장하면

현재 PHP 실습을 현대적인 웹 서비스 구조로 바꾸면 다음처럼 이해할 수 있다.

~~~text
React
↓
HTTP Request
↓
FastAPI
↓
SQL
↓
PostgreSQL
↓
FastAPI
↓
JSON
↓
React
↓
DOM
~~~

역할은 달라지지 않는다.

~~~text
PHP 실습                 현대적 구조

HTML/JS            →     React
Apache + PHP       →     Web Server + FastAPI
MySQL              →     PostgreSQL
HTML Response      →     JSON Response + Frontend Rendering
~~~

기술이 바뀌어도 **요청 → 처리 → DB → 응답 → 화면**이라는 큰 구조는 같다.

---

# 10. SQL JOIN의 역할

웹 화면에서는 ID보다 사람이 읽을 수 있는 이름이 필요하다.

예를 들어 enrollments 테이블이 다음처럼 저장될 수 있다.

~~~text
student_id = 101
course_id  = 3
~~~

DB에서는 ID가 효율적이지만 화면에서는:

~~~text
김학생
데이터베이스 기초
~~~

처럼 보여야 한다.

그래서 JOIN을 사용한다.

~~~text
students
   ↑
enrollments
   ↓
courses
~~~

JOIN은 **서로 다른 테이블의 관계를 연결해 필요한 정보를 한 결과로 만드는 것**이다.

---

# 11. ON / WHERE / ORDER BY 실행 사고

초보 단계에서는 다음처럼 기억하면 이해하기 쉽다.

~~~text
FROM / JOIN
→ 어떤 테이블을 사용할지 결정

ON
→ 두 테이블을 어떤 기준으로 연결할지 결정

WHERE
→ 연결된 데이터 중 필요한 행을 필터링

ORDER BY
→ 최종 결과의 표시 순서를 정렬
~~~

예:

~~~sql
SELECT ...
FROM students s
JOIN enrollments e
  ON s.id = e.student_id
WHERE ...
ORDER BY ...
~~~

ON은 **연결 기준**, WHERE는 **필터**, ORDER BY는 **정렬**이다.

---

# 12. PDO와 Prepared Statement

PHP가 MySQL과 통신할 때 PDO를 사용할 수 있다.

~~~text
PHP
↓ PDO
MySQL
~~~

Prepared Statement는 SQL과 사용자 입력값을 분리해서 처리하는 방식이다.

개념:

~~~text
SQL 구조
+
사용자 입력값
↓
안전하게 Binding
↓
DB 실행
~~~

장점:
- SQL Injection 위험 감소
- 입력값 처리 명확
- 반복 Query 처리에 유리

실무에서는 사용자 입력을 SQL 문자열에 직접 이어붙이는 방식보다 Prepared Statement를 사용하는 것이 기본이다.

---

# 13. DBeaver를 먼저 사용하는 이유

웹 페이지에서 SQL 오류가 발생하면 원인이 여러 곳일 수 있다.

~~~text
PHP 문제?
DB 연결 문제?
SQL 문법 문제?
JOIN 문제?
변수 문제?
~~~

그래서 SQL 자체를 먼저 DBeaver에서 실행해 본다.

~~~text
DBeaver SQL 성공
+
PHP 실패
↓
SQL 자체보다는 PHP/PDO/변수/연결 부분을 우선 확인
~~~

즉 DBeaver는 단순 DB GUI가 아니라 **문제 범위를 줄이는 검증 도구**로 사용할 수 있다.

---

# 14. 오류가 발생했을 때 확인 순서

오늘 가장 실무적으로 중요한 부분이다.

웹 서비스 오류를 한꺼번에 보지 말고 계층별로 확인한다.

~~~text
1. Browser
↓
2. Network / HTTP
↓
3. Web Server
↓
4. Backend
↓
5. Database Connection
↓
6. SQL
~~~

## 1단계 Browser

확인:
- 화면이 열리는가
- Console 오류가 있는가
- 404가 발생하는가

## 2단계 Network

DevTools Network에서 확인:
- Request URL
- Method
- Status Code
- Response
- 요청이 실제 전송되었는가

## 3단계 Apache

확인:
- Apache 서비스 실행 여부
- 요청 포트가 열려 있는가
- Document Root가 맞는가

일반적인 HTTP 기본 포트는 80이다.

## 4단계 PHP

확인:
- Parse Error
- Fatal Error
- 변수명
- include 경로
- PDO 코드

## 5단계 MySQL

확인:
- DB 서비스 실행 여부
- 접속정보
- DB명
- 사용자 권한
- 포트

MySQL의 일반적인 기본 포트는 3306이다.

## 6단계 SQL

DBeaver에서 Query를 직접 실행한다.

~~~text
DBeaver에서도 실패
→ SQL / Schema / Data 문제 가능성

DBeaver에서는 성공
PHP에서는 실패
→ PHP / PDO / DB 연결 / 변수 문제 가능성
~~~

이런 방식으로 장애 범위를 좁혀야 한다.

---

# 15. 서버 종류를 적재적소에 사용하는 기준

서버라는 단어는 한 종류의 프로그램을 뜻하지 않는다.

## Web Server

예: Apache, Nginx

~~~text
Browser의 HTTP/HTTPS 요청을 받는 입구
~~~

사용:
- 정적 파일 제공
- HTTPS
- Reverse Proxy
- 요청 전달

## Application Server / Backend

예: FastAPI, Django, Spring, PHP Runtime

~~~text
실제 업무 로직 처리
~~~

사용:
- 로그인
- 주문
- 회원
- 결제
- API

## Database Server

예: PostgreSQL, MySQL

~~~text
서비스 데이터 저장
~~~

## File Server

파일 저장과 전달을 담당한다.

예:
- 업로드 파일
- 문서
- 이미지
- 백업

## SSH Server

Ubuntu 같은 서버를 원격 관리할 때 사용한다.

일반적인 SSH 기본 포트는 22다.

~~~text
관리자 PC
↓ SSH
Ubuntu Server
~~~

## SFTP

SSH 연결 위에서 안전하게 파일을 전송한다.

~~~text
SFTP
= SSH 기반 File Transfer
~~~

FTP와 달리 SSH 암호화 채널을 사용하므로 서버 운영에서는 일반적으로 SFTP가 더 적합하다.

---

# 16. HTTPS와 Domain

서비스를 외부에 공개하면 사용자가 IP와 포트를 직접 입력하게 하는 것보다 Domain과 HTTPS를 사용하는 구조가 일반적이다.

~~~text
사용자
↓
https://service.example
↓
DNS
↓
Public IP
↓
Firewall / NAT
↓
443
↓
Web Server / Reverse Proxy
↓
Application
~~~

역할:

- Domain: 사람이 기억하기 쉬운 서비스 주소
- DNS: Domain을 IP로 변환
- HTTPS: HTTP 통신 암호화
- TLS Certificate: 서버 신원과 암호화에 사용
- Port 443: HTTPS의 일반적인 기본 포트

---

# 17. Port를 이해해야 하는 이유

한 서버에서도 여러 서비스가 동시에 동작할 수 있다.

예:

~~~text
22   → SSH / SFTP
80   → HTTP
443  → HTTPS
3306 → MySQL
5432 → PostgreSQL
8000 → 개발용 Application Server에서 자주 사용하는 예시 포트
~~~

포트는 같은 서버 안에서 **어떤 서비스로 요청을 보낼지 구분하는 번호**라고 이해할 수 있다.

단, 운영에서는 DB 포트를 외부 인터넷에 무조건 공개하지 않는다. 필요한 네트워크와 사용자만 접근하도록 제한하는 것이 기본이다.

---

# 18. OAuth는 어디에 위치하는가

OAuth 로그인은 단순 화면 기능이 아니다.

~~~text
Browser
↓
우리 서비스
↓
OAuth Provider
↓
사용자 인증
↓
Callback
↓
우리 Backend
↓
사용자 Session / Account 처리
~~~

OAuth Provider는 등록된 Redirect URI를 기준으로 인증 결과를 돌려준다.

운영환경에서는 Domain과 HTTPS가 OAuth 설정과 밀접하게 연결된다.

Client Secret, Access Token, Refresh Token 같은 값은 소스코드나 공개 TIL에 기록하면 안 된다.

~~~text
OAUTH_CLIENT_ID=***
OAUTH_CLIENT_SECRET=***
ACCESS_TOKEN=***
REFRESH_TOKEN=***
~~~

---

# 19. Ubuntu 운영 관점으로 연결

개발 PC에서 코드가 실행된다고 서비스 운영이 끝나는 것은 아니다.

운영 서버에서는 최소 다음을 확인해야 한다.

~~~text
Ubuntu
├─ Network
├─ Firewall
├─ SSH/SFTP
├─ Web Server
├─ Application
├─ Database Connection
├─ Domain/DNS
├─ HTTPS Certificate
├─ Process
├─ Log
└─ Deployment
~~~

장애 발생 시:

~~~text
사용자 화면
→ DNS
→ Network
→ Port
→ HTTPS
→ Web Server
→ Backend
→ DB
→ 외부 API/OAuth
~~~

순으로 계층을 나누어 보는 습관이 중요하다.

---

# 20. 오늘 배운 내용과 서버 운영의 연결

오늘 Frontend 실습에서 Network 탭으로 GET 요청을 본 것은 앞으로 서버 장애를 분석할 때 그대로 사용된다.

예:

~~~text
Network에 요청 자체가 없음
→ Frontend Event / JavaScript 확인

요청은 있는데 404
→ URL / Routing / Web Server 확인

500
→ Backend Log 확인

Backend는 정상인데 데이터 없음
→ DB Query / 조건 확인

OAuth Redirect 실패
→ Domain / HTTPS / Redirect URI 확인
~~~

즉 DevTools는 Frontend 개발자만 쓰는 도구가 아니라 **Frontend와 Backend 사이의 경계를 확인하는 운영 도구**이기도 하다.

---

# 21. 현업 장애진단 체크리스트

## Browser
- URL이 맞는가
- Console Error가 있는가
- Network 요청이 발생하는가

## Network
- DNS가 정상인가
- 서버 IP까지 접근 가능한가
- 필요한 Port가 열려 있는가

## HTTPS
- 인증서가 유효한가
- Domain과 인증서가 일치하는가

## Web Server
- Apache/Nginx가 실행 중인가
- Virtual Host / Reverse Proxy 설정이 맞는가

## Backend
- Process가 실행 중인가
- Routing이 맞는가
- Application Log에 오류가 있는가

## Database
- DB Process가 실행 중인가
- 연결정보가 맞는가
- 권한이 있는가
- SQL이 단독 실행되는가

## OAuth / 외부 API
- Redirect URI가 맞는가
- Secret/Token이 환경변수로 관리되는가
- Callback 요청이 Backend까지 도착하는가

---

# 22. 오늘의 실무 관점

웹 개발을 공부할 때 HTML, PHP, SQL을 각각 외우는 것보다 다음 흐름을 머릿속에 먼저 만드는 것이 중요하다.

~~~text
사용자
↓
Browser
↓
HTTP/HTTPS
↓
Web Server
↓
Backend
↓
SQL
↓
Database
↓
Backend
↓
HTML 또는 JSON
↓
Browser
~~~

오류도 이 흐름에서 **어디까지 성공했고 어디부터 실패했는가**를 찾으면 된다.

이 방식은 WAMP 실습뿐 아니라 React + FastAPI + PostgreSQL, Django, Ubuntu 배포 환경에서도 그대로 사용할 수 있다.

---

# 23. 다음 학습 포인트

1. HTTP Status Code 200 / 404 / 500
2. GET / POST / PUT / DELETE
3. REST API
4. JSON Request / Response
5. Apache와 Nginx 차이
6. Reverse Proxy
7. localhost와 Server IP 차이
8. DNS가 Domain을 IP로 바꾸는 과정
9. HTTPS/TLS 인증서
10. Ubuntu에서 Process와 Port 확인
11. SSH와 SFTP 실습
12. PostgreSQL/MySQL 연결 장애 진단
13. OAuth Callback 흐름
14. 개발환경과 운영환경 차이

---

# 보안 기록 원칙

공개 저장소 TIL에는 실제 서비스 접속정보나 인증정보를 남기지 않는다.

~~~text
SERVER_IP=***
SSH_USER=***
SSH_PASSWORD=***
DB_HOST=***
DB_USER=***
DB_PASSWORD=***
API_KEY=***
ACCESS_TOKEN=***
WEBHOOK_URL=***
OAUTH_CLIENT_SECRET=***
.env 값=***
~~~

개념 학습에 필요한 포트 번호와 프로토콜은 기록할 수 있지만, 실제 운영 서버의 IP·계정·비밀번호·Secret은 기록하지 않는다.

---

# 오늘의 한 줄 정리

> **웹 개발의 핵심은 화면 하나를 만드는 것이 아니라 Browser → HTTP → Web Server → Backend → Database → Response 전체 흐름을 이해하고, 장애가 났을 때 어느 계층에서 끊겼는지 찾아내는 것이다.**
