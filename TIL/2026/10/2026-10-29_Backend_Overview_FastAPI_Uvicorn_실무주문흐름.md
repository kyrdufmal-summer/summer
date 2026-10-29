# TIL | 2026-10-29 — Backend Overview: FastAPI·Uvicorn·Reverse Proxy와 기업형 주문 시스템의 요청 흐름

> **학습 범위:** Phase 02 Backend Overview 수업 화면 및 후속 학습 대화  
> **학습 목표:** Browser → Frontend → (Reverse Proxy) → Uvicorn/FastAPI → 업무 계층 → PostgreSQL의 책임과 장애 지점을 실무 사례로 설명한다.  
> **보안:** 아래 쇼핑몰 '가상상점'은 가상 사례다. 실제 고객·회사·서버·계정·인증정보·기업 기밀은 포함하지 않았다.  
> **검증 범위:** 제공된 수업 화면에서 확인한 개념과 설명을 바탕으로 정리한 학습 기록이다. 코드 실행, HTTP 테스트, DB 접속 및 부하 시험을 실제로 완료했다는 의미가 아니다.

## 1. 핵심 결론

- **Frontend**는 고객에게 화면을 보여주고 입력을 받아 API를 호출한다.
- **Backend**는 접근 권한, 입력 검증, 업무 규칙, DB 접근을 통제한다.
- **PostgreSQL**은 데이터를 영구 저장하고 관계·무결성·트랜잭션을 관리한다.
- **Uvicorn은 ASGI 서버**, **FastAPI는 API 프레임워크**다. Uvicorn은 HTTP 연결을 받아 ASGI 애플리케이션에 전달하고, FastAPI는 정의된 라우트와 처리 코드를 실행한다.
- **Reverse Proxy**는 운영 규모에 따라 앞단에 둘 수 있는 선택적 구성요소로, HTTPS 종료·요청 분배·보안 정책 등을 수행할 수 있다.
- 기술을 나열하는 것보다 **누가 요청을 받고, 누가 판단하고, 누가 저장하고, 어디서 실패했는지** 설명하는 것이 중요하다.

## 2. 문제 정의 — 왜 화면만으로 회사 업무를 처리할 수 없을까?

가상의 커머스 기업 '가상상점'을 생각한다.

고객이 운동화 한 켤레를 구매할 때 단순히 버튼을 누르는 데서 끝나지 않는다.

1. 고객이 로그인한 상태인지 확인한다.
2. 상품과 옵션이 실제로 존재하는지 조회한다.
3. 요청한 수량이 유효한지 검증한다.
4. 최신 재고를 확인하고 다른 고객의 동시 주문과 충돌하지 않도록 조정한다.
5. 주문 금액을 서버의 신뢰 가능한 가격 기준으로 계산한다.
6. 주문과 재고 변경을 원자적으로 처리한다.
7. 실패하면 변경사항을 되돌리고 고객에게 명확한 오류를 알려준다.

만약 이 규칙을 브라우저의 JavaScript만 믿고 처리하면 사용자가 요청을 조작할 수 있고, 여러 브라우저 사이의 동시성도 안전하게 제어하기 어렵다. 그래서 **브라우저는 DB에 직접 접근하지 않고, 백엔드가 데이터와 권한을 통제**하도록 설계한다.

## 3. 구조와 용어 — 전체 요청 흐름

```text
[사용자 / 브라우저]
        │ 화면 표시·입력
        ▼
[Frontend: HTML/CSS/JavaScript 또는 React/Next.js]
        │ HTTPS + REST API 방식의 HTTP 요청 / JSON
        ▼
[Reverse Proxy / HTTPS 종료]  ← 운영 필요에 따른 선택 구성
        │ HTTP 전달 (구체적인 보안/네트워크 구성은 환경에 따라 다름)
        ▼
[Uvicorn: HTTP 연결을 처리하는 ASGI 서버]
        │ ASGI 요청 전달
        ▼
[FastAPI 애플리케이션]
        ├─ Router/Endpoint : 경로와 HTTP 메서드 연결
        ├─ Pydantic        : 요청·응답 스키마, 입력 검증
        ├─ Service         : 유스케이스 실행, 업무 절차
        └─ Repository      : DB 조회·저장 추상화
                   │ SQLAlchemy 등을 이용해 SQL 실행
                   ▼
             [PostgreSQL]
          영구 저장 · 제약조건 · 트랜잭션
```

위 그림은 학습을 위한 대표적인 논리 구조다. 실제 서비스에서는 인증 미들웨어, Domain 계층, 외부 결제사, 메시지 큐, 캐시, 로드밸런서 등이 더해질 수 있다.

### 3.1 Frontend는 무엇을 하는가?

- 고객에게 상품 목록과 주문 버튼을 표시한다.
- 수량 입력을 받아 서버의 API를 호출한다.
- API 응답의 성공/실패 상태를 화면에 보여준다.
- UX 차원의 사전 입력 검증은 가능하지만, **최종 업무 검증은 서버 책임**이다.

**회사 실무 예시:** 고객이 수량을 2개로 선택하면 프론트엔드는 `POST /orders` 요청을 전송한다. 가격, 재고, 최종 주문 허용 여부는 서버가 결정한다.

### 3.2 HTTP / REST API / JSON의 차이

| 용어 | 담당하는 것 | 주문 시스템 예시 |
|---|---|---|
| HTTP/HTTPS | 요청·응답 통신 규칙 / 암호화된 전송 | POST 요청과 응답 상태 코드 |
| REST 스타일 API | 리소스와 HTTP 메서드를 활용한 인터페이스 설계 방식 | `POST /orders`, `GET /orders/{id}` |
| JSON | 데이터를 표현하는 형식 | `{"product_id": 101, "quantity": 2}` |
| API Contract | 요청·응답·상태 코드의 팀 간 약속 | 주문 성공 201, 입력 오류 422 등 |

REST와 JSON은 같은 말이 아니다. REST 스타일 API가 반드시 JSON만 쓰는 것도 아니다.

### 3.3 Uvicorn이란?

**비유:** Uvicorn은 고객 전화가 들어올 수 있도록 전화 회선을 운영하고 담당 애플리케이션에 연결하는 접수 시스템이다. FastAPI는 연결된 요청을 어떤 코드가 처리할지 결정하는 업무 애플리케이션이다.

- Uvicorn: HTTP 연결·ASGI 프로토콜 처리, FastAPI 애플리케이션 실행
- FastAPI: 경로 매칭, 의존성 처리, 데이터 검증, 지정된 Python 코드 실행
- PostgreSQL: 주문 데이터 영구 저장

```powershell
uvicorn main:app --reload
```

| 조각 | 의미 |
|---|---|
| `uvicorn` | ASGI 서버 실행 |
| `main` | `main.py` 모듈 |
| `app` | 모듈 내부 FastAPI 애플리케이션 객체 |
| `--reload` | 개발 중 파일 변경 시 자동 재시작 |

**빠뜨리면?** FastAPI 코드만 정의했다고 네트워크 서버가 자동으로 뜨지는 않는다. Uvicorn 또는 다른 호환 ASGI 서버 등으로 실행해야 한다. **운영 환경에서는 개발 전용 `--reload`를 사용하지 않는 것이 일반적**이다.

### 3.4 Reverse Proxy는 왜 있는가?

**비유:** 회사 건물의 안내 데스크. 어느 서비스로 요청을 전달할지 결정하고, 보안 출입 절차를 적용할 수 있다.

회사 실무에서 Reverse Proxy가 맡을 수 있는 일:

- HTTPS 인증서 적용 및 TLS 종료
- 경로·도메인별 요청 라우팅
- 일부 접근 제한, 요청 크기 제한, 로깅
- 여러 서버 인스턴스로 트래픽 분배(설정에 따라)

```text
인터넷 고객
    ↓ HTTPS
Nginx / 클라우드 프록시
    ↓ 내부 네트워크
Uvicorn + FastAPI 프로세스
```

**주의:** Reverse Proxy가 모든 환경에 필수인 것은 아니다. 작은 개발 환경에서는 브라우저가 Uvicorn에 직접 연결할 수 있다. Reverse Proxy와 로드밸런서는 개념적으로 겹치는 기능이 있지만 항상 동일한 것은 아니다.

### 3.5 Router · Pydantic · Service · Repository · SQLAlchemy

| 구성 | 역할 | 가상상점에서의 질문 |
|---|---|---|
| Router/Endpoint | URL·HTTP 메서드를 특정 처리 함수로 연결 | `POST /orders`는 어디로 갈까? |
| Pydantic | 타입·형식·필드 제약을 검증 | `quantity`가 올바른 양의 정수인가? |
| Service | 주문 생성 유스케이스와 업무 절차 조율 | 재고 확인 후 주문을 어떻게 생성할까? |
| Domain(설계 선택) | 순수 핵심 업무 규칙과 상태 제약 | 재고 부족이면 주문을 허용할 수 있는가? |
| Repository | DB 읽기·쓰기 인터페이스 | 옵션 재고를 어떻게 조회할까? |
| SQLAlchemy | SQL 생성·실행 및 ORM 등을 지원하는 라이브러리 | Python 코드에서 DB와 어떻게 통신할까? |
| PostgreSQL | 실제 데이터 저장·제약·트랜잭션 | 주문 기록과 재고의 일관성을 어떻게 지킬까? |

**Pydantic의 검증과 업무 판단은 다르다.** 수량으로 `"사과"`가 오거나 음수가 오면 입력 스키마가 거절할 수 있다. 반면 `quantity=100`이 형식상 맞더라도 재고 3개라면 Service/Domain의 업무 규칙에서 거절해야 한다.

**Repository는 SQLAlchemy의 다른 이름이 아니다.** Repository는 아키텍처상 책임·추상화이며 SQLAlchemy는 이를 구현할 때 쓸 수 있는 기술이다.

## 4. 실무 시나리오 A — 정상 주문의 End-to-End 처리

**가정:** 고객 A가 상품 101을 2개 주문한다. 이 회사는 FastAPI + PostgreSQL을 운영하며, 재고는 서버에서 관리한다.

1. 브라우저에서 고객이 주문 버튼을 누른다.
2. Frontend가 `POST /orders` 요청을 HTTPS로 보낸다.
3. Reverse Proxy가 구성된 운영 환경이라면 외부 HTTPS를 처리하고 요청을 애플리케이션 서버로 전달한다.
4. Uvicorn이 요청을 받아 FastAPI에 전달한다.
5. Router가 `POST /orders` 엔드포인트를 선택한다.
6. Pydantic이 요청 JSON의 필드·타입·제약을 확인한다.
7. 인증·인가 로직이 주문 가능한 사용자 요청인지 검사한다.
8. Service가 주문 생성 절차를 실행한다.
9. Repository가 상품과 최신 재고를 조회한다.
10. 업무 규칙을 만족하면 DB 트랜잭션에서 주문 기록과 재고 변경을 일관되게 수행한다.
11. DB 작업이 성공적으로 커밋되면 결과를 JSON으로 응답한다.
12. Frontend가 고객에게 주문 성공 상태를 표시한다.

**관측 기준:** HTTP 상태 코드, 주문 ID, DB 주문 행, 재고 변경, 서버 로그의 요청 식별자가 서로 일치해야 한다.

## 5. 실무 시나리오 B — 재고 부족과 잘못된 입력은 어떻게 다른가?

| 상황 | 검증 위치 | 대표 응답 |
|---|---|---|
| `quantity=-1` | Pydantic 필드 제약 | 422 Unprocessable Content |
| 존재하지 않는 상품 | Service/Repository 조회 결과 → API 예외 매핑 | 404 Not Found |
| 재고 3개인데 100개 요청 | Service/Domain 업무 판단 | 409 Conflict (팀 계약에 따름) |
| 비로그인 접근 | 인증 레이어 | 401 Unauthorized |
| 로그인했지만 권한 부족 | 인가 레이어 | 403 Forbidden |
| 예상하지 못한 서버 오류 | 예외 처리·운영 계층 | 500 Internal Server Error |

**중요:** 409는 모든 재고 부족 상황에서 자동으로 발생하는 정답 코드가 아니라 **해당 팀의 API 계약에 따라 선택하는 예시**다. FastAPI는 기본 입력 검증 실패에 보통 422를 사용한다.

**실무 포인트:** 고객에게는 “재고가 부족합니다”라고 안내하되, 내부 DB 연결 문자열이나 예외 스택은 노출하지 않는다.

## 6. 실무 시나리오 C — 마지막 한 개를 두 사람이 동시에 주문한다면?

**문제:** 재고 1개. 고객 A와 B가 거의 동시에 주문 요청을 보낸다.

위험한 흐름:

```text
A: 재고 조회 → 1개
B: 재고 조회 → 1개
A: 주문 성공
B: 주문 성공
결과: 실제 재고를 초과하는 주문 가능성
```

이를 방지하는 한 가지 접근이 PostgreSQL 트랜잭션과 행 잠금(`SELECT ... FOR UPDATE`)이다.

```sql
BEGIN;
SELECT stock FROM product_options
WHERE id = 101
FOR UPDATE;
-- 잠근 최신 행을 기반으로 수량을 검증
-- 조건을 만족하면 주문 생성 및 재고 감소
COMMIT;
```

이 SQL은 **설명용 의사 절차**로, 실제 서비스의 전체 주문 SQL이 아니다. 행 잠금이 적용되는 트랜잭션 범위, 동일한 DB 세션 사용, 오류 시 롤백, 잠금 순서, 타임아웃 등을 함께 설계해야 한다.

**확인할 결과:** 두 요청 중 허용된 수량만큼만 성공하고, 재고가 음수가 되지 않으며, 실패한 주문의 중간 데이터가 남지 않아야 한다.

## 7. 실무 시나리오 D — 서비스 장애가 났을 때 어디를 볼까?

| 고객의 증상 | 우선 확인 영역 | 1차 조치 예시 |
|---|---|---|
| 사이트가 아예 열리지 않음 | DNS/TLS/Reverse Proxy/프론트 호스팅 | 상태·인증서·라우팅 확인 |
| API 연결 실패 / 502 | Reverse Proxy와 Uvicorn/프로세스 | 서버 생존·포트·업스트림 연결 확인 |
| 특정 API가 404 | Router·URL·리소스 존재 여부 | 요청 경로와 리소스 구분 |
| 잘못된 주문 데이터 422 | Pydantic 및 클라이언트 요청 | 필드·타입·요청 JSON 확인 |
| 재고 부족인데 주문 성공 | Service/Domain·DB 동시성 | 규칙·락·트랜잭션 검사 |
| 주문 성공 응답인데 저장 누락 | Service/Repository/DB 트랜잭션 | 커밋 시점과 DB 기록 검증 |
| 응답이 느림 | DB 쿼리·외부 API·서버 자원 | 요청 추적·실행 계획·지표 확인 |

**장애 대응 절차:** 사용자 영향 파악 → 최근 배포 확인 → 요청 ID로 로그 추적 → 실패 계층 격리 → 안전한 복구 → 재발 방지 테스트 및 모니터링 추가.

## 8. 기초 실습 코드 — 요청 검증부터 응답까지

다음은 교육용 최소 예제다. **주문 저장이나 실결제 기능은 없다.** `main.py`로 저장한다고 가정한다.

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class OrderRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/orders")
def create_order(order: OrderRequest):
    return {
        "product_id": order.product_id,
        "quantity": order.quantity,
        "message": "입력 형식 검증 완료 — DB 저장은 하지 않음"
    }
```

환경에 필요한 패키지를 설치한 뒤 다음으로 실행할 수 있다.

```powershell
python -m pip install fastapi uvicorn
uvicorn main:app --reload
```

브라우저에서 `http://127.0.0.1:8000/docs`로 Swagger UI를 열고 `POST /orders` 요청을 시험한다.

**시험 입력 예시(실제 실행 결과가 아닌 예상 동작):**

- `{"product_id":101,"quantity":2}` → 200, 입력 검증 완료 응답
- `{"product_id":101,"quantity":-1}` → 422, 양수 제약 위반
- `{"product_id":"abc","quantity":2}` → 422, 정수 해석 실패
- `GET /health` → 200, `{"status":"ok"}`

**검증 기준:** 올바른 요청과 오류 요청에서 HTTP 상태 및 JSON 응답을 확인한다. 이 실습만으로 주문/재고/트랜잭션 안정성을 검증했다고 간주하지 않는다.

**주의:** Swagger UI의 Execute는 실제 HTTP 요청을 보낸다. 실제 쓰기 API에서는 테스트 DB와 안전한 데이터를 사용해야 한다.

## 9. 백엔드 4계층 아키텍처와 연결하기

웹 시스템의 **Frontend / Backend / Database**는 서비스 전반의 큰 구분이다. 반면 **Presentation / Application / Domain / Infrastructure**는 백엔드 코드 내부의 책임 분리다.

| 백엔드 내부 계층 | 넣는 것 | 피할 것 |
|---|---|---|
| Presentation | FastAPI Router, Pydantic 스키마, HTTP 오류 매핑 | 복잡한 주문/재고 규칙 |
| Application | 주문 유스케이스, 처리 순서, 트랜잭션 경계 | HTTP 응답 포맷에 강하게 종속 |
| Domain | 주문 상태 전이, 재고 부족 판단 등 핵심 규칙 | FastAPI 요청 객체·DB 세션 직접 의존 |
| Infrastructure | Repository 구현, SQLAlchemy, DB 연결 | 비즈니스 규칙을 무분별하게 복제 |

**왜 나누는가?** 화면이나 DB 접근 방식이 바뀌어도 업무 규칙을 독립적으로 검증하기 쉽고, 장애의 책임 지점을 좁힐 수 있다. 다만 작은 실습에 과도한 추상화를 도입하면 코드 탐색·유지보수 비용이 늘어난다.

## 10. 선택의 장단점과 트레이드오프

| 선택 | 장점 | 비용/위험 | 권장되는 상황 |
|---|---|---|---|
| FastAPI | Python 중심 API 작성, 스키마 검증·문서 자동화 | 설계·인증·트랜잭션은 별도 책임 | Python 백엔드/API |
| Uvicorn | ASGI 애플리케이션 서비스 | 운영 프로세스·확장 관리 필요 | FastAPI 실행 |
| Reverse Proxy | TLS·라우팅·정책 중앙화 | 운영 구성요소 증가 | 다양한 서비스/운영 요구 |
| Pydantic | 입출력 규격 검증 | 모든 업무 규칙을 대신하지 못함 | API 데이터 계약 |
| SQLAlchemy | DB 접근 코드 구조화 | ORM 학습·SQL 성능 이해 필요 | 관계형 DB 연계 |
| PostgreSQL | 관계·제약·트랜잭션 기능 | 백업·모니터링·마이그레이션 관리 | 일관성이 중요한 업무 데이터 |
| 4계층 분리 | 테스트 용이성·변경 영향 통제 | 파일/추상화 증가 | 규칙이 복잡하고 확장 가능성 있는 서비스 |

**유의:** PostgreSQL은 DBMS이고 Supabase는 PostgreSQL을 포함한 관리형 백엔드 서비스 플랫폼이다. 양자를 완전히 대체 관계로 단순화할 수 없다. 4계층을 만들기 위해 반드시 특정 DB 플랫폼을 포기해야 하는 것도 아니다.

## 11. 위험 요소와 재발 방지

- **개인정보·비밀정보:** 실제 고객 이름·전화번호·주소, 기업 내부 URL, 인증정보, 토큰, 비밀번호, .env 내용은 TIL에 기록하지 않는다. 예시로 필요하면 `***`로 마스킹한다.
- **입력 검증 ≠ 권한 검증:** Pydantic 검증을 통과해도 접근 권한이 없으면 처리하면 안 된다.
- **200 응답 ≠ DB 저장 완료:** 테스트 코드의 성공 응답을 실DB 커밋 성공과 혼동하지 않는다.
- **동시성:** 재고는 화면에서 보던 오래된 숫자가 아니라 동일 트랜잭션에서 검증한 최신 상태를 기준으로 판단한다.
- **트랜잭션:** 여러 데이터 변경이 하나의 업무 단위라면 commit/rollback 경계를 명시한다.
- **운영 보안:** 내부 예외·SQL·연결 정보는 클라이언트에 보내지 않는다.
- **회귀 테스트:** 정상/검증 실패/권한 실패/재고 부족/동시 요청을 분리해 테스트한다.
- **관측 가능성:** 요청 ID, 오류 코드, 처리 시간, DB 연결 상태를 기록하되 개인정보는 최소화한다.

## 12. 회사 실무 체크리스트

- [ ] API 요청/응답 스키마와 상태 코드 계약을 문서화했는가?
- [ ] 입력 검증과 업무 규칙 검증을 구분했는가?
- [ ] 최종 가격·재고·권한을 서버가 검증하는가?
- [ ] 주문과 재고 변경이 일관된 트랜잭션으로 처리되는가?
- [ ] 동시 주문 시 초과 판매가 발생하지 않도록 방어했는가?
- [ ] 실패 시 롤백과 사용자 친화적 오류 응답이 있는가?
- [ ] API 서버 장애와 DB 장애를 구분해 관측할 수 있는가?
- [ ] 개발·테스트·운영 환경의 접근 권한을 분리했는가?
- [ ] Swagger 테스트가 운영 데이터를 변경하지 않도록 보호했는가?
- [ ] 로그와 문서에 개인정보/회사 기밀이 들어가지 않았는가?

## 13. 오늘의 회고

오늘은 웹 화면에서 시작한 하나의 주문이 어떻게 서버와 DB를 거치는지 전체 지도로 정리했다.

특히 Uvicorn을 **업무 규칙을 판단하는 주체**가 아니라 **HTTP 요청과 FastAPI 애플리케이션을 연결하는 서버**로 구분했다. Router는 경로를 찾고, Pydantic은 요청 데이터의 형식과 제약을 검사하고, Service/Domain은 업무 허용 여부를 판단하고, Repository/SQLAlchemy는 DB 접근을 구현한다. PostgreSQL은 실제 데이터를 보관하며 트랜잭션 및 무결성 기능을 제공한다.

앞으로 새로운 기술을 만나면 다음 질문부터 하기로 한다.

1. **왜 필요한가?** 어떤 업무 문제를 해결하는가?
2. **없으면 어떻게 되는가?** 대안은 무엇인가?
3. **누가 책임지는가?** HTTP 연결, 입력 검증, 업무 판단, DB 저장 중 어디인가?
4. **어떻게 검증하는가?** 정상·오류·동시성·장애 시나리오에서 무엇이 확인돼야 하는가?

### 다음 학습 과제(미실행)

1. `/health`와 `/orders`를 로컬 Uvicorn으로 실행한다.
2. Swagger UI에서 정상 JSON/음수 수량/문자형 ID 요청을 비교한다.
3. API 요청 → 라우터 → 서비스 → DB 흐름도를 직접 다시 그린다.
4. 나중에 DB 연동 단계에서 트랜잭션과 동시성 테스트를 추가한다.

## 14. 참고 자료 및 근거

- 제공된 **Phase 02 Backend Overview** 수업 화면: Frontend / Backend / PostgreSQL, Uvicorn·Pydantic·SQLAlchemy 학습 목표.
- 제공된 **웹 요청 흐름 및 백엔드 구성요소** 수업 화면: Browser, Reverse Proxy, Router, Schema, Service, Repository, PostgreSQL.
- 2026-10-29 학습 대화에서 정리한 Uvicorn 역할, 주문 사례, HTTP 요청 흐름 및 오류 위치.
- FastAPI 공식 문서: https://fastapi.tiangolo.com/
- Uvicorn 공식 문서: https://www.uvicorn.org/
- Pydantic 공식 문서: https://docs.pydantic.dev/
- SQLAlchemy 공식 문서: https://docs.sqlalchemy.org/
- PostgreSQL 공식 문서: https://www.postgresql.org/docs/

> **출처 경계:** 앞서 전달된 네이버 블로그 및 Google Drive 원문은 본문 확인이 되지 않아 인용하거나 그 내용을 읽은 것으로 기록하지 않았다. 위 실무 시나리오와 코드는 학습 목적의 가상 예제이며, 운영 시스템 실행·검증 증빙이 아니다.
