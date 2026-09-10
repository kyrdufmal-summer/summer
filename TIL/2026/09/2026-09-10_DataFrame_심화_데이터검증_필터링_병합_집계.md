# 2026-09-10 TIL — DataFrame 심화: 데이터 검증, 필터링, 병합, 집계

## 1. 오늘의 핵심

오늘은 Pandas의 DataFrame을 단순히 `read_csv()`로 읽고 출력하는 수준에서 끝내지 않고,
실제 데이터 분석 업무에서 사용하는 흐름으로 연결해서 학습했다.

오늘 가장 중요하게 잡은 흐름은 다음과 같다.

```text
CSV 파일
↓
pd.read_csv()
↓
DataFrame 생성
↓
데이터 구조 확인
↓
결측치 / 중복 / ID / 타입 검증
↓
필터링 / 정렬 / 파생 컬럼 생성
↓
여러 DataFrame 병합
↓
groupby 집계
↓
집계 결과 검증
↓
CSV 또는 분석 결과로 저장
```

즉, DataFrame은 단순한 표가 아니라
**원본 데이터를 분석 가능한 상태로 만들고, 관계를 연결하고, 결과를 검증하는 작업 단위**라고 이해했다.

---

# 2. CSV를 DataFrame으로 읽는 흐름

기본 형태는 다음과 같다.

```python
import pandas as pd

customers = pd.read_csv("data/raw/customers.csv")
```

하지만 실제 프로젝트에서는 Notebook의 현재 위치에 따라 상대경로가 달라질 수 있다.

예를 들어 Notebook이 다음 위치에 있다면,

```text
notebooks/ch04/03.ipynb
```

단순히 다음처럼 작성했을 때

```python
pd.read_csv("raw/customers.csv")
```

현재 작업 디렉터리가 예상과 다르면 파일을 찾지 못할 수 있다.

오늘은 이미 프로젝트에 만들어 둔 경로 유틸을 활용하는 방식으로 해결했다.

```python
from course_utils.paths import find_project_root

PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data" / "raw"

customers = pd.read_csv(DATA_DIR / "customers.csv")
```

이 방식의 장점은 Notebook이 어느 하위 폴더에서 실행되더라도
프로젝트 루트를 기준으로 데이터 경로를 만들 수 있다는 점이다.

### 오늘 정리

```text
잘못된 접근
현재 Notebook 위치를 기준으로 ../.. 를 계속 계산

더 좋은 접근
프로젝트 루트를 찾는 공통 util 사용
→ PROJECT_ROOT
→ DATA_DIR
→ 실제 파일 경로 생성
```

실무에서는 하드코딩한 절대경로보다 프로젝트 기준 경로를 만드는 방식을 더 많이 사용한다.

---

# 3. DataFrame을 받으면 제일 먼저 확인할 것

DataFrame을 불러왔다고 바로 분석하면 안 된다.
먼저 데이터의 모양과 타입을 확인해야 한다.

## 3-1. 행과 열의 개수

```python
df.shape
```

예시 결과:

```text
(100, 5)
```

의미:

```text
100행
5열
```

---

## 3-2. 앞부분 확인

```python
df.head()
```

기본값은 앞에서 5행이다.

```python
df.head(10)
```

처럼 원하는 개수를 지정할 수 있다.

---

## 3-3. 뒷부분 확인

```python
df.tail()
```

데이터 마지막 부분이 정상적으로 들어왔는지 확인할 때 사용한다.

---

## 3-4. 컬럼명 확인

```python
df.columns
```

컬럼 이름 오타나 예상하지 못한 컬럼이 있는지 확인한다.

---

## 3-5. 데이터 타입 확인

```python
df.dtypes
```

또는

```python
df.info()
```

`info()`는 다음을 한 번에 확인하기 좋다.

```text
행 개수
컬럼명
결측치 여부
데이터 타입
메모리 사용량
```

### 핵심

숫자처럼 보여도 실제 dtype이 `object`일 수 있고,
날짜처럼 보여도 문자열일 수 있다.

따라서 분석 전에 타입 확인이 반드시 필요하다.

---

# 4. Series와 DataFrame 차이

Pandas에서 가장 헷갈리기 쉬운 부분 중 하나다.

```python
df["city"]
```

결과는 **Series**다.

```python
type(df["city"])
```

```text
pandas.core.series.Series
```

반면,

```python
df[["city"]]
```

결과는 **DataFrame**이다.

차이는 대괄호 개수다.

```text
df["city"]
→ Series


df[["city"]]
→ DataFrame
```

여러 컬럼을 선택할 때는 반드시 리스트 형태로 넣는다.

```python
df[["name", "city", "age"]]
```

---

# 5. 결측치 확인

결측치는 값이 비어 있는 상태다.

Pandas에서는 대표적으로 다음처럼 확인한다.

```python
df.isna()
```

하지만 전체 표가 True/False로 나오기 때문에 보통 다음처럼 사용한다.

```python
df.isna().sum()
```

예시:

```text
name        0
age         3
city        1
```

의미:

```text
age 결측치 3개
city 결측치 1개
```

### 왜 확인해야 하는가?

평균, 합계, 그룹 집계, 모델 학습 등에 영향을 줄 수 있기 때문이다.

---

# 6. 범주형 데이터의 결측값과 mode()[0]

`embarked`처럼 문자열/범주형 데이터는 평균을 계산할 수 없다.

이런 경우 대표값으로 최빈값을 사용할 수 있다.

```python
df["embarked"].mode()
```

`mode()`의 결과는 하나의 값이 아니라 **Series 형태**다.

예를 들어:

```text
0    S
```

여기서 `[0]`은 숫자 0을 결측치에 넣는다는 뜻이 아니다.

```python
df["embarked"].mode()[0]
```

의미는

```text
mode() 결과 중 첫 번째 값 가져오기
```

이다.

즉 결과가 `S`라면 실제 반환값은 `S`다.

```python
mode_value = df["embarked"].mode()[0]
```

이후 다음처럼 사용할 수 있다.

```python
df["embarked"] = df["embarked"].fillna(mode_value)
```

### 오늘 헷갈렸던 부분

```text
[0] = 0을 넣는다 X
[0] = 결과의 첫 번째 위치 값을 꺼낸다 O
```

---

# 7. 중복 데이터 확인

```python
df.duplicated()
```

중복 개수 확인:

```python
df.duplicated().sum()
```

중복 제거:

```python
df.drop_duplicates()
```

그러나 무조건 제거하는 것이 아니라
업무적으로 정말 중복인지 먼저 확인해야 한다.

예를 들어 주문 데이터는 같은 고객이 같은 날 여러 번 주문할 수 있기 때문에
고객 ID가 중복된다고 해서 잘못된 데이터는 아니다.

### 핵심

```text
중복값 발견
≠ 무조건 오류

업무 의미를 확인한 뒤 판단해야 함
```

---

# 8. ID 무결성 확인

업무 데이터에는 ID가 매우 중요하다.

예:

```text
customers.customer_id
orders.order_id
orders.customer_id
products.product_id
order_items.product_id
```

ID는 보통 다음을 확인해야 한다.

```text
1. 결측값이 있는가
2. 중복되면 안 되는 ID가 중복됐는가
3. 다른 테이블의 외래키 값이 실제 원본 테이블에 존재하는가
```

예:

```python
customers["customer_id"].isna().sum()
```

```python
customers["customer_id"].duplicated().sum()
```

이렇게 데이터 관계가 깨져 있는지 확인할 수 있다.

---

# 9. 조건 필터링

DataFrame에서 조건을 만족하는 행만 가져올 수 있다.

```python
df[df["age"] >= 30]
```

흐름은 다음과 같다.

```text
df["age"] >= 30
↓
각 행마다 True / False 생성
↓
df[조건]
↓
True인 행만 남김
```

예:

```python
condition = df["age"] >= 30
filtered = df[condition]
```

조건을 변수로 분리하면 코드의 의미가 더 잘 보인다.

---

# 10. 여러 조건 결합

AND 조건:

```python
df[(df["age"] >= 30) & (df["city"] == "Seoul")]
```

OR 조건:

```python
df[(df["city"] == "Seoul") | (df["city"] == "Busan")]
```

Pandas에서는 Python의 `and`, `or` 대신

```text
&
|
```

를 사용한다.

각 조건은 괄호로 감싸는 것이 중요하다.

---

# 11. isin()으로 여러 값 찾기

다음처럼 OR 조건을 여러 번 쓰는 대신,

```python
(df["city"] == "Seoul") | (df["city"] == "Busan")
```

`isin()`을 사용할 수 있다.

```python
df[df["city"].isin(["Seoul", "Busan"])]
```

의미:

```text
city 값이 Seoul 또는 Busan 목록 안에 있는가?
```

---

# 12. 틸드(~)로 조건 반전하기

`~`는 Boolean 조건을 반대로 뒤집는다.

```python
~df["city"].isin(["Seoul", "Busan"])
```

의미:

```text
Seoul 또는 Busan이 아닌 데이터
```

따라서 다음처럼 사용할 수 있다.

```python
df[~df["city"].isin(["Seoul", "Busan"])]
```

---

# 13. 정렬

```python
df.sort_values("age")
```

기본은 오름차순이다.

내림차순:

```python
df.sort_values("age", ascending=False)
```

여러 컬럼 정렬:

```python
df.sort_values(["city", "age"])
```

업무에서는 매출 상위, 재고 부족 순서, 최신 주문 순서 등을 볼 때 자주 사용한다.

---

# 14. Copy-on-Write(CoW)와 안전한 수정

오늘 중요한 개념 중 하나였다.

DataFrame을 필터링한 뒤 그 결과를 수정할 때
원본과 복사본 관계가 애매하면 문제가 생길 수 있다.

예:

```python
filtered = df[df["age"] >= 30]
filtered["group"] = "adult"
```

Pandas에서는 이런 코드가 상황에 따라 예상하지 못한 수정이나 경고로 이어질 수 있다.

따라서 수정할 DataFrame을 만들 때 명시적으로 복사하는 습관이 좋다.

```python
filtered = df[df["age"] >= 30].copy()
filtered["group"] = "adult"
```

### 정리

```text
조회만 한다
→ 단순 필터 가능

필터 결과를 수정한다
→ .copy() 권장
```

Copy-on-Write 환경에서도 명시적으로 데이터 수정 의도를 드러내는 것이 안전하다.

---

# 15. 날짜 데이터 변환

CSV에서 읽은 날짜는 문자열인 경우가 많다.

```python
df["order_date"].dtype
```

결과가 `object`라면 날짜형으로 변환할 수 있다.

```python
df["order_date"] = pd.to_datetime(df["order_date"])
```

잘못된 날짜가 섞여 있을 가능성이 있다면:

```python
df["order_date"] = pd.to_datetime(
    df["order_date"],
    errors="coerce"
)
```

`errors="coerce"`는 변환할 수 없는 값을 `NaT`로 만든다.

따라서 변환 후 반드시 다시 확인해야 한다.

```python
df["order_date"].isna().sum()
```

---

# 16. 파생 컬럼 만들기

기존 컬럼을 이용해 새로운 컬럼을 만들 수 있다.

예:

```python
order_items["line_total"] = (
    order_items["quantity"] * order_items["unit_price"]
)
```

의미:

```text
수량 × 단가 = 주문상세별 금액
```

날짜에서 월을 만들 수도 있다.

```python
orders["order_month"] = orders["order_date"].dt.to_period("M")
```

파생 컬럼은 원본 데이터를 삭제하는 것이 아니라
분석에 필요한 의미 있는 값을 새롭게 만드는 과정이다.

---

# 17. merge — 여러 DataFrame 연결하기

실제 업무 데이터는 하나의 DataFrame에 모든 정보가 들어 있지 않다.

예:

```text
customers
products
orders
order_items
```

각각 다른 업무 정보를 가지고 있다.

주문 데이터와 상품 데이터를 연결하려면 `merge()`를 사용한다.

```python
merged = order_items.merge(
    products,
    on="product_id",
    how="left"
)
```

SQL로 생각하면 JOIN과 비슷하다.

```text
Pandas merge
≈ SQL JOIN
```

---

# 18. merge에서 validate 사용하기

단순히 merge가 실행됐다고 데이터가 정상이라는 뜻은 아니다.

관계가 예상과 맞는지 검증해야 한다.

예:

```python
merged = order_items.merge(
    products,
    on="product_id",
    how="left",
    validate="many_to_one"
)
```

`many_to_one`의 의미:

```text
order_items 쪽
→ 같은 product_id 여러 개 가능

products 쪽
→ product_id 하나당 한 행이어야 함
```

즉 관계가 예상과 다르면 Pandas가 오류를 발생시켜 준다.

이것은 단순한 실행보다 훨씬 안전한 방식이다.

---

# 19. merge 결과를 indicator로 검증

```python
merged = order_items.merge(
    products,
    on="product_id",
    how="left",
    indicator=True
)
```

그러면 `_merge` 컬럼이 생성된다.

대표 값:

```text
both
left_only
right_only
```

의미:

```text
both
→ 양쪽 DataFrame에서 정상 매칭

left_only
→ 왼쪽에는 있지만 오른쪽에는 없음

right_only
→ 오른쪽에는 있지만 왼쪽에는 없음
```

따라서 미매칭 데이터를 직접 찾을 수 있다.

```python
merged[merged["_merge"] != "both"]
```

---

# 20. merge 전후 행 수 검증

실무에서는 merge 결과의 행 수를 반드시 확인하는 습관이 중요하다.

```python
len(order_items)
len(merged)
```

예상하지 못하게 행 수가 늘어난다면
조인 대상 테이블의 키가 중복되었을 가능성이 있다.

예:

```text
order_items = 1,000행
merge 결과 = 1,350행
```

이라면 무조건 정상이라고 보기 어렵다.

### 핵심

```text
merge 성공
≠ 데이터 관계 정상
```

다음까지 확인해야 한다.

```text
행 수
키 중복
미매칭
관계 cardinality
```

---

# 21. groupby — 그룹별 집계

`groupby()`는 특정 기준별로 데이터를 묶어서 계산한다.

예:

```python
category_sales = (
    merged
    .groupby("category")["line_total"]
    .sum()
)
```

의미:

```text
category별로 묶고
각 그룹의 line_total을 합계
```

---

# 22. agg()로 여러 집계를 한 번에 하기

실무에서는 합계 하나보다 여러 지표를 동시에 계산하는 경우가 많다.

예:

```python
category_summary = (
    merged
    .groupby("category")
    .agg(
        quantity_sold=("quantity", "sum"),
        total_sales=("line_total", "sum"),
        order_count=("order_id", "nunique"),
        customer_count=("customer_id", "nunique"),
    )
    .reset_index()
)
```

결과는 다음과 같은 의미를 가진다.

```text
quantity_sold
→ 판매 수량

total_sales
→ 총 매출

order_count
→ 주문 건수

customer_count
→ 구매 고객 수
```

이렇게 집계하면 단순한 표가 아니라
업무 의사결정에 사용할 수 있는 요약 데이터가 된다.

---

# 23. count와 nunique 차이

매우 중요하다.

```python
df["order_id"].count()
```

은 값의 개수를 세고,

```python
df["order_id"].nunique()
```

는 중복을 제거한 고유값 개수를 센다.

예를 들어 한 주문에 상품이 3개 있으면 `order_items`에는 같은 `order_id`가 3번 존재할 수 있다.

```text
order_id
1001
1001
1001
```

이때

```text
count() = 3
nunique() = 1
```

주문 건수를 구할 때는 보통 `nunique()`가 더 적절하다.

---

# 24. 범주형 데이터 빈도 확인

문자열 값이 어떤 형태로 들어 있는지 확인할 때 `value_counts()`를 사용한다.

```python
orders["status"].value_counts()
```

예를 들어 다음처럼 들어 있을 수 있다.

```text
Complete
completed
Cancelled
```

사람이 보기에는 `Complete`와 `completed`가 같은 뜻일 수 있지만
컴퓨터는 서로 다른 문자열로 본다.

따라서 분석 전에 값의 표기 규칙을 확인해야 한다.

### 핵심

```text
문자열은 사람의 의미가 아니라
실제 저장된 문자 그대로 비교된다.
```

---

# 25. 이상치(Outlier)와 Box Plot

이상치는 다른 값들에 비해 유난히 크거나 작은 값이다.

예를 들어 대부분의 운임이 낮은 범위에 있는데
일부 값만 매우 크다면 이상치일 수 있다.

Box Plot에서는 보통 상자와 수염 범위를 크게 벗어난 값이 점으로 표시된다.

```python
df["fare"].plot.box()
```

이상치가 있다고 해서 무조건 삭제하는 것은 아니다.

실제 고가 구매, 고액 주문, VIP 고객 등 정상적인 업무 데이터일 수도 있다.

따라서 다음 순서로 판단해야 한다.

```text
이상치 발견
↓
입력 오류인지 확인
↓
실제 업무상 가능한 값인지 확인
↓
분석 목적에 따라 유지/보정/제외 판단
```

---

# 26. DataFrame과 Python 기본 반복문의 관계

오늘 복습 문제에서는 Pandas 집계 메서드만 사용하는 것이 아니라
DataFrame에서 값을 꺼낸 뒤 Python 기본 반복문으로 직접 계산하는 흐름도 확인했다.

예:

```python
ages = df["age"].tolist()

total = 0

for age in ages:
    total += age
```

이 과정을 통해 다음 관계를 다시 이해했다.

```text
DataFrame
→ 데이터를 표 형태로 관리

Series
→ 한 컬럼

list / dict
→ Python 기본 자료구조

for
→ 여러 값을 하나씩 처리

if
→ 각 값에 대한 조건 판단
```

Pandas가 내부적으로 편리하게 처리해 주는 작업도
결국 데이터 하나하나를 판단하고 계산하는 논리 위에 있다.

---

# 27. 직접 최댓값/최솟값을 찾는 사고방식

Pandas에서는 다음처럼 간단하게 할 수 있다.

```python
df["date"].max()
```

하지만 Python 기본 로직으로 직접 구현하면 알고리즘 구조를 이해할 수 있다.

```python
latest = dates[0]

for date in dates:
    if date > latest:
        latest = date
```

핵심 흐름:

```text
기준값 하나 잡기
↓
하나씩 반복
↓
현재 값과 비교
↓
조건에 맞으면 기준값 교체
```

이 구조는 최솟값, 최대 금액, 최고 점수 등 다양한 문제에 그대로 사용할 수 있다.

---

# 28. 오늘 다시 연결한 Python 문제 풀이 구조

문제를 보면 바로 코드를 쓰기보다 다음 순서로 구조화하는 것이 도움이 된다.

```text
1. 어떤 데이터가 주어졌는가?
2. 여러 개인 것은 무엇인가?
3. 무엇을 하나씩 반복해야 하는가?
4. 무엇을 판단해야 하는가?
5. 계산하거나 바꿔야 하는 값은 무엇인가?
6. 최종적으로 무엇을 출력해야 하는가?
```

이 구조는 DataFrame 문제에도 그대로 적용된다.

예를 들어:

```text
고객 데이터가 주어짐
↓
여러 고객이 있음
↓
고객을 하나씩 확인
↓
구매 금액 조건 판단
↓
무료배송 여부 결정
↓
결과 출력
```

Pandas를 쓰더라도 결국 문제 구조를 먼저 이해해야 한다.

---

# 29. DataFrame 분석에서 가장 중요한 것은 검증

오늘 공부하면서 가장 크게 느낀 부분은
**코드가 실행되는 것과 분석 결과가 맞는 것은 다른 문제**라는 점이다.

예:

```python
merged = a.merge(b)
```

코드가 에러 없이 실행돼도

```text
행이 예상보다 늘어났을 수 있음
ID가 매칭되지 않았을 수 있음
중복 데이터가 섞였을 수 있음
문자열 표기가 달라 그룹이 분리됐을 수 있음
날짜 변환 실패가 발생했을 수 있음
```

따라서 분석 코드는 다음처럼 구성해야 한다.

```text
처리
→ 확인
→ 검증
→ 다음 처리
```

단순히 마지막 결과만 보는 것이 아니라
중간중간 데이터 상태를 확인하는 것이 중요하다.

---

# 30. 오늘의 실무형 DataFrame 분석 흐름

오늘 공부한 내용을 실제 분석 순서로 다시 정리하면 다음과 같다.

## STEP 1. 프로젝트 경로 확인

```python
PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data" / "raw"
```

## STEP 2. CSV 로딩

```python
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
order_items = pd.read_csv(DATA_DIR / "order_items.csv")
```

## STEP 3. 구조 확인

```python
customers.shape
customers.head()
customers.info()
customers.dtypes
```

## STEP 4. 데이터 품질 확인

```python
customers.isna().sum()
customers.duplicated().sum()
customers["customer_id"].duplicated().sum()
```

## STEP 5. 범주형 값 확인

```python
orders["status"].value_counts()
```

## STEP 6. 날짜 변환

```python
orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce"
)
```

## STEP 7. 조건 필터

```python
completed_orders = orders[
    orders["status"] == "completed"
].copy()
```

## STEP 8. 파생 컬럼 생성

```python
completed_orders["order_month"] = (
    completed_orders["order_date"].dt.to_period("M")
)
```

## STEP 9. 병합

```python
merged = order_items.merge(
    products,
    on="product_id",
    how="left",
    validate="many_to_one",
    indicator=True
)
```

## STEP 10. 병합 검증

```python
merged["_merge"].value_counts()
```

```python
len(order_items), len(merged)
```

## STEP 11. 금액 계산

```python
merged["line_total"] = (
    merged["quantity"] * merged["unit_price"]
)
```

## STEP 12. 그룹 집계

```python
summary = (
    merged
    .groupby("category")
    .agg(
        quantity_sold=("quantity", "sum"),
        total_sales=("line_total", "sum")
    )
    .reset_index()
)
```

## STEP 13. 최종 검증

```python
summary["total_sales"].sum()
merged["line_total"].sum()
```

두 값이 같은지 확인한다.

이 마지막 검증까지 해야 분석 결과에 신뢰를 가질 수 있다.

---

# 31. 오늘 발생했던 오류와 해결 방식

## 문제 1. CSV 파일 경로 오류

### 원인

Notebook의 현재 실행 위치와 CSV 파일 위치가 다름.

### 해결

프로젝트 공통 경로 util 사용.

```python
from course_utils.paths import find_project_root
```

```python
PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data" / "raw"
```

### 배운 점

절대경로를 개인 PC 기준으로 박아 두기보다
프로젝트 기준 경로를 사용하는 것이 제출 및 협업에 더 안전하다.

---

## 문제 2. `mode()[0]`의 `[0]` 의미 혼동

### 원인

`[0]`을 값 0을 넣는 코드로 이해함.

### 실제 의미

```text
mode()가 반환한 Series의 첫 번째 값을 선택
```

### 배운 점

메서드의 반환 타입을 먼저 확인하면 코드 해석이 쉬워진다.

---

## 문제 3. 필터된 DataFrame 수정

### 위험

필터 결과를 바로 수정하면 원본과의 관계가 불명확할 수 있음.

### 해결

```python
filtered = df[condition].copy()
```

### 배운 점

조회와 수정은 구분해서 생각한다.

---

## 문제 4. merge가 되면 끝이라고 생각하기 쉬움

### 위험

키 중복이나 미매칭으로 행 수가 바뀔 수 있음.

### 해결

```python
validate="many_to_one"
indicator=True
```

그리고 병합 전후 행 수를 비교한다.

---

# 32. 오늘의 핵심 용어 정리

| 용어 | 오늘 이해한 의미 |
|---|---|
| DataFrame | 행과 열로 구성된 2차원 데이터 구조 |
| Series | DataFrame의 한 컬럼과 같은 1차원 데이터 구조 |
| shape | 행/열 개수 |
| dtypes | 각 컬럼의 데이터 타입 |
| isna() | 결측값 확인 |
| duplicated() | 중복 확인 |
| value_counts() | 범주형 값별 개수 확인 |
| isin() | 여러 후보 값 중 포함 여부 확인 |
| `~` | Boolean 조건 반전 |
| copy() | 별도의 DataFrame으로 명확히 복사 |
| to_datetime() | 문자열 등을 날짜 타입으로 변환 |
| merge() | 여러 DataFrame 연결 |
| validate | merge 관계가 예상과 맞는지 검사 |
| indicator | merge 매칭 상태 확인 |
| groupby() | 특정 기준으로 데이터를 그룹화 |
| agg() | 그룹별 여러 집계 계산 |
| count() | 값의 개수 |
| nunique() | 고유값 개수 |
| Outlier | 다른 값과 크게 차이나는 이상치 |

---

# 33. 오늘의 이해 변화

이전에는 Pandas를

```text
CSV 읽기
→ 컬럼 선택
→ 평균/합계 구하기
```

정도로 생각했다.

오늘은 다음처럼 이해가 확장됐다.

```text
파일 위치를 안정적으로 찾고
↓
데이터를 DataFrame으로 읽고
↓
구조와 타입을 확인하고
↓
결측/중복/ID를 검증하고
↓
조건에 맞는 데이터만 안전하게 복사하고
↓
필요한 파생 컬럼을 만들고
↓
여러 테이블을 관계에 맞게 연결하고
↓
그룹별 지표를 집계하고
↓
마지막으로 결과가 원본 데이터와 논리적으로 맞는지 검증한다
```

즉 Pandas의 핵심은 메서드 암기보다
**데이터 흐름과 검증 순서를 이해하는 것**이라고 정리했다.

---

# 34. 다음 학습 때 체크할 것

- `loc`, `iloc` 차이 직접 실습
- `groupby()` 결과가 Series/DataFrame으로 달라지는 경우 확인
- `merge()`의 `inner`, `left`, `right`, `outer` 비교
- PK/FK 개념과 Pandas merge 관계 연결
- 결측치 처리 시 평균/중앙값/최빈값 선택 기준
- Box Plot의 IQR 기준 계산 원리
- `pivot_table()`과 `groupby()` 차이
- 데이터 전처리 전후 행 수를 자동 검증하는 코드 작성

---

# 35. 오늘의 한 줄 회고

> DataFrame은 표를 다루는 도구가 아니라, 데이터를 읽고 구조를 확인하고 관계를 연결한 뒤 결과가 맞는지 검증하는 전체 분석 흐름의 중심 도구다.

---

## 보안 기록

오늘 TIL에는 API Key, Token, Password, Webhook URL 등 민감정보를 기록하지 않았다.
민감정보가 필요한 경우 실제 값 대신 아래와 같이 기록한다.

```text
API_KEY=***
PASSWORD=***
TOKEN=***
WEBHOOK_URL=***
```
