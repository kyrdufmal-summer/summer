# 2026-09-27 TIL — 관계 데이터 집계와 Graph 사고의 출발점

## 오늘의 핵심

오늘은 전화번호 관계 데이터를 이용해 **한 대상 번호가 몇 명의 서로 다른 피해 번호와 연결되는지** 집계하는 문제를 Python과 SQL 두 방식으로 정리했다.

단순히 개수를 세는 연습처럼 보이지만, 실제로는 다음 사고를 연습한 것이다.

~~~text
원본 이벤트
→ 관계 추출
→ 중복 제거
→ 관계 수 집계
→ 임계값 필터
→ 계정/소유자 정보 연결
→ 조사 우선순위 생성
~~~

이 구조는 이후 Fraud Detection, 보이스피싱 네트워크 분석, VOC 관계분석, Graph Analytics로 확장할 수 있다.

---

# 1. Python에서 관계를 표현하는 방법

전화번호별로 여러 피해 전화번호가 연결될 수 있다.

예를 들어:

~~~text
target_phone A
→ victim 1
→ victim 2
→ victim 2
→ victim 3
~~~

여기서 단순 리스트 길이를 세면 victim 2가 두 번 포함되어 잘못 집계될 수 있다.

그래서 관계 집계에서는 **중복 제거가 핵심**이다.

Python에서는 다음 자료구조 조합이 자연스럽다.

~~~text
딕셔너리
key   = 조사 대상 전화번호
value = 연결된 피해 전화번호들의 집합(set)
~~~

같은 피해자가 같은 번호로 여러 번 신고될 수 있기 때문에 relation count는 사건 행 수가 아니라 **중복 없는 연결 대상 수**로 정의해야 한다.

---

# 2. Python의 구조화 사고

오늘 문제를 6단계로 정리하면 다음과 같다.

1. 데이터: 조사 대상 전화번호, 피해 전화번호, 신고/통화/사건 기록
2. 반복: 사건 데이터를 한 건씩 확인
3. 조건: target_phone과 victim_phone이 유효한지 확인
4. 관계 저장: target_phone별로 victim_phone을 set에 추가
5. 계산: 각 target_phone의 set 크기를 계산
6. 출력: 피해 번호가 2명 이상 연결된 target_phone만 출력

즉:

~~~text
데이터
→ 반복
→ 관계 저장
→ 중복 제거
→ 개수 계산
→ 조건 필터
→ 출력
~~~

이다.

---

# 3. 관계 데이터에서 행 수와 관계 수는 다르다

실무에서 중요한 구분이다.

사건 테이블에 10행이 있다고 해서 관계가 10개인 것은 아니다. 같은 연결이 반복 기록될 수 있기 때문이다.

~~~text
event row count
≠
unique relationship count
~~~

그래서 관계 분석에서는 먼저 무엇을 세는지 명확히 해야 한다.

- 사건 건수인가
- 서로 다른 피해자인가
- 서로 다른 기기인가
- 서로 다른 계좌인가
- 동일 관계의 반복 횟수인가

이 기준을 잘못 정하면 Risk Score나 운영지표가 틀어진다.

---

# 4. SQL에서는 COUNT(DISTINCT)가 같은 역할을 한다

Python에서 set이 중복을 제거했다면 SQL에서는 COUNT(DISTINCT victim_phone)가 같은 역할을 한다.

개념 흐름:

~~~text
phone_events
↓
target_phone별 그룹
↓
COUNT(DISTINCT victim_phone)
↓
피해자 수 계산
↓
2명 이상만 필터
~~~

핵심은 단순 COUNT가 아니라 **중복 없는 피해 전화번호 수**를 세는 것이다.

---

# 5. 왜 CTE를 사용했는가

오늘 SQL에서는 CTE(Common Table Expression)를 활용해 관계 집계와 최종 조회를 분리했다.

~~~text
1단계: target_phone별 victim_count 계산
2단계: victim_count가 기준 이상인 번호만 추림
3단계: phone_accounts와 JOIN
4단계: owner_name 등 업무정보 추가
~~~

CTE의 장점은 복잡한 SQL을 의미 있는 단계로 쪼갤 수 있다는 것이다.

~~~text
raw relationship
→ aggregated relationship
→ filtered target
→ enriched business result
~~~

이렇게 나누면 Root Cause를 찾기도 쉽고, 운영자가 결과를 이해하기도 쉽다.

---

# 6. GROUP BY와 COUNT(DISTINCT)의 관계

SQL에서 target_phone별 피해자 수를 구하려면 target_phone 단위로 그룹을 만든다.

그 그룹 안에서 COUNT(DISTINCT victim_phone)를 계산한다.

이 구조는 관계분석의 가장 기본적인 형태다.

~~~text
Node A
→ 몇 개의 서로 다른 Node B와 연결되어 있는가?
~~~

Graph 용어로 보면 이것은 Degree에 가까운 기초 Feature다.

---

# 7. 2명 이상이라는 조건의 의미

victim_count >= 2 같은 조건은 단순 필터가 아니라 **조사 우선순위를 만드는 Rule**이다.

~~~text
피해자 1명 연결
→ 개별 사건 가능성

피해자 2명 이상 연결
→ 반복 패턴 가능성

피해자 10명 이상 연결
→ 우선 조사 후보
~~~

다만 숫자가 많다고 범죄자로 단정하면 안 된다. 정상적인 콜센터 번호나 대표번호일 수도 있기 때문이다.

따라서 관계 수는 **Risk Signal이지 결론이 아니다.**

---

# 8. phone_accounts JOIN이 필요한 이유

관계 수만 보면 target_phone과 피해자 수 정도만 알 수 있다. 하지만 운영/조사에서는 실제 소유자 또는 계정정보가 필요하다.

~~~text
target_phone
owner_name
victim_count
~~~

그래서 관계 집계 결과를 phone_accounts 같은 기준 테이블과 JOIN한다.

~~~text
Analytics Result
+
Master Data
=
Actionable Result
~~~

즉 분석 결과만으로는 부족하고, **업무에서 바로 쓸 수 있는 소유자·계정·조직 정보까지 붙여야 한다.**

---

# 9. RDBMS 안에서도 Graph 사고를 시작할 수 있다

Graph DB가 없어도 PostgreSQL만으로 관계 분석의 첫 단계를 충분히 할 수 있다.

~~~text
1-hop
전화번호 → 피해자
→ GROUP BY + COUNT(DISTINCT)

2-hop
전화번호 → Device → Account
→ JOIN 여러 번

3-hop 이상
→ Recursive CTE 또는 Graph DB 고려
~~~

즉 SQL JOIN은 관계 탐색의 시작이고, Recursive CTE는 다단계 관계 탐색, Graph DB는 관계 중심 탐색과 패턴 분석 강화로 이해할 수 있다.

---

# 10. 보이스피싱 조사로 확장하면

~~~text
target_phone
→ victim_phone
→ account
→ device
→ ip
~~~

초기 SQL에서는 전화번호별 피해자 수만 보지만 이후에는 다음으로 확장할 수 있다.

- 전화번호별 공유 Device 수
- 전화번호별 공유 계좌 수
- 전화번호별 공통 IP 수
- 피해자간 공통 송금계좌

이렇게 되면 단순 집계가 **관계형 Risk Feature Engineering**으로 발전한다.

---

# 11. Data Science 관점

오늘의 victim_count도 하나의 Feature다.

예:

~~~text
victim_count
shared_device_count
shared_account_count
shared_ip_count
transaction_velocity
fraud_neighbor_count
recent_call_count
~~~

단일 Feature보다 여러 관계 Feature를 조합하는 것이 False Positive를 줄이는 데 유리하다.

---

# 12. 운영 관점에서 필요한 화면

분석 결과가 있어도 운영자가 사용할 수 없으면 가치가 떨어진다.

관리자 화면에는 최소 다음 정보가 필요하다.

~~~text
대상 전화번호
소유자
연결 피해자 수
연결 피해자 목록
공유 Device
공유 계좌
공유 IP
최근 사건 시각
Risk Score
주요 Risk 근거
조사 상태
담당자
~~~

그리고 상세 관계 보기, 사건 연결, 조사 Case 생성, 오탐 표시, 추가 증거 요청, 차단 요청, 조사 완료 같은 Action이 필요하다.

즉:

~~~text
분석
→ 화면
→ 판단
→ Action
→ Feedback
~~~

까지 가야 한다.

---

# 13. VOC 운영과 연결

같은 사고를 VOC에도 적용할 수 있다.

~~~text
VOC A → payment API
VOC B → payment API
VOC C → release 2.4.1
VOC D → server X
~~~

개별 VOC만 보면 서로 다른 문의처럼 보이지만 관계로 묶으면:

~~~text
VOC
→ API
→ Release
→ Server
→ Root Cause
~~~

가 된다.

그러면 반복 VOC를 단순 카테고리 집계가 아니라 **하나의 기술 원인 네트워크**로 볼 수 있다.

---

# 14. IT영업에서 설명하는 방법

고객에게 Graph DB를 도입하자고 바로 말하기보다 다음 순서가 좋다.

~~~text
현재 문제
→ 데이터가 여러 시스템에 흩어짐

운영 문제
→ 사건마다 여러 화면과 Excel을 확인

숨은 비용
→ 조사시간 증가 / 중복조사 / 누락

관계 기반 해결
→ 공통 고객·기기·계좌·전화번호 자동 연결

운영 Action
→ Alert / Case / Investigation

성과
→ 조사시간↓ / 반복VOC↓ / 손실금액↓
~~~

즉 제품을 파는 것이 아니라 **문제를 푸는 데이터 구조를 제안**해야 한다.

---

# 15. 오늘의 실무 포인트

## 데이터베이스
- 기준 Entity를 먼저 정의한다.
- 어떤 관계를 세는지 명확히 한다.
- COUNT(*)와 COUNT(DISTINCT ...)를 구분한다.
- JOIN 결과 중복을 항상 의심한다.
- Master Data와 Analytics 결과를 연결한다.

## 데이터사이언스
- 관계 수를 Feature로 만든다.
- 하나의 Feature만으로 판단하지 않는다.
- 시간·금액·빈도를 함께 본다.
- False Positive Feedback을 기록한다.

## 운영
- Score만 보여주지 않는다.
- 왜 위험한지 근거를 보여준다.
- Case Owner를 지정한다.
- Action 결과를 다시 데이터로 남긴다.

## IT영업
- DB 제품명부터 말하지 않는다.
- 고객의 조사시간과 누수부터 묻는다.
- PoC 범위를 좁힌다.
- KPI를 기술지표가 아니라 비용·시간·손실로 잡는다.

---

# 16. 오늘 배운 점

첫째, Python의 set과 SQL의 COUNT(DISTINCT)는 서로 다른 문법이지만 **중복 없는 관계 수를 세는 같은 문제**를 해결한다.

둘째, 관계형 DB의 JOIN은 Graph 사고의 출발점이 될 수 있다.

셋째, victim_count 같은 단순 집계도 이후 Graph Feature와 Risk Model의 입력으로 확장할 수 있다.

넷째, 분석 결과는 운영자가 판단하고 Action할 수 있도록 계정정보·소유자·근거와 연결되어야 한다.

다섯째, IT영업에서는 Graph DB를 파는 것이 아니라 **분리된 데이터를 연결해 조사시간과 운영 누수를 줄이는 구조**를 제안해야 한다.

---

# 다음에 연습할 포인트

- PostgreSQL Recursive CTE로 2-hop 관계 찾기
- 동일 Device를 공유하는 전화번호 찾기
- 동일 계좌를 공유하는 사건 묶기
- Python NetworkX로 관계 시각화
- Degree Centrality 계산
- Community Detection
- 관계 기반 Risk Score 만들기
- VOC → API → Release 관계 모델링

---

# 보안 기록 원칙

실제 전화번호, 계좌번호, IP, 고객식별정보, API Key, 토큰, 비밀번호, Webhook URL, DB 접속정보는 공개 TIL에 기록하지 않는다.

~~~text
PHONE=***
ACCOUNT=***
IP=***
DB_PASSWORD=***
API_KEY=***
WEBHOOK_URL=***
~~~

---

# 오늘의 한 줄 정리

> **관계 데이터 분석의 시작은 복잡한 Graph AI가 아니라, 어떤 Entity가 어떤 다른 Entity와 중복 없이 몇 번 연결되는지를 정확히 세는 것부터 시작한다.**