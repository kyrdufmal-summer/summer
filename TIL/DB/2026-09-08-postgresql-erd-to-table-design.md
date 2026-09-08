# 2026-09-08 PostgreSQL ERD를 실제 테이블로 변환하기

## 오늘 학습한 내용

오늘은 주문 시스템을 예제로 ERD를 설계하고 이를 PostgreSQL 테이블 구조로 연결했다.

기본 엔터티는 다음 네 개다.

```text
Customers
Menus
Orders
OrderDetails
```

관계는 다음과 같다.

```text
Customers
    │
    │ 1 : N
    ▼
Orders
    │
    │ 1 : N
    ▼
OrderDetails
    ▲
    │ N : 1
    │
Menus
```

고객 한 명은 여러 주문을 만들 수 있고, 주문 하나에는 여러 메뉴가 포함될 수 있다.

특히 `Orders`와 `Menus`를 바로 연결하지 않고 `OrderDetails`라는 중간 테이블을 사용하는 이유를 학습했다.

예를 들어 한 주문이 다음과 같다면:

```text
주문 #1

아메리카노 × 2
샌드위치 × 1
케이크 × 1
```

`Orders`에는 주문 자체가 한 행으로 저장되고, `OrderDetails`에는 실제 주문 메뉴가 세 행으로 저장된다.

## PK와 FK

모든 테이블의 PK는 자동 증가하는 정수값을 사용하기로 했다.

PostgreSQL에서는 다음과 같이 만들 수 있다.

```sql
id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

따라서 INSERT할 때 직접 `id`를 넣지 않아도 PostgreSQL이 자동으로 번호를 생성한다.

예:

```text
1
2
3
4
...
```

테이블 간 관계는 FK로 연결한다.

```text
orders.customer_id
        ↓
customers.id
```

```text
order_details.order_id
        ↓
orders.id
```

```text
order_details.menu_id
        ↓
menus.id
```

이 때문에 테이블 생성 순서 역시 중요하다.

```text
1. customers
2. menus
3. orders
4. order_details
```

참조 대상 테이블을 먼저 생성한 후 FK를 가진 테이블을 생성해야 한다.

## 별도 Schema를 사용하는 이유

현재 `ai_database_book` 데이터베이스에는 기본 `public` 스키마가 있지만, ERD 학습 테이블은 별도의 스키마로 분리하기로 했다.

```sql
CREATE SCHEMA erd_practice;
```

구조는 다음과 같다.

```text
PostgreSQL
└─ ai_database_book
      │
      ├─ public
      │
      └─ erd_practice
             ├─ customers
             ├─ menus
             ├─ orders
             └─ order_details
```

DB를 새로 만드는 것이 아니라 **하나의 데이터베이스 내부에서 학습 영역을 논리적으로 분리**하는 것이다.

## 실제 CREATE TABLE 설계

### customers

```sql
CREATE TABLE erd_practice.customers (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    address VARCHAR(255),
    email VARCHAR(255),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### menus

```sql
CREATE TABLE erd_practice.menus (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price INTEGER NOT NULL,
    category VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

### orders

```sql
CREATE TABLE erd_practice.orders (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INT NOT NULL,
    ordered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT '주문완료',
    total_amount INTEGER NOT NULL DEFAULT 0,
    total_quantity INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES erd_practice.customers(id)
);
```

### order_details

```sql
CREATE TABLE erd_practice.order_details (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INT NOT NULL,
    menu_id INT NOT NULL,
    quantity INTEGER NOT NULL,
    sale_price INTEGER NOT NULL,

    CONSTRAINT fk_order_details_order
        FOREIGN KEY (order_id)
        REFERENCES erd_practice.orders(id),

    CONSTRAINT fk_order_details_menu
        FOREIGN KEY (menu_id)
        REFERENCES erd_practice.menus(id)
);
```

## 판매 당시 가격을 별도로 저장하는 이유

오늘 ERD에서 중요한 설계 포인트 중 하나는 다음 두 컬럼이었다.

```text
menus.price
order_details.sale_price
```

처음에는 가격이 중복처럼 보일 수 있지만 의미가 다르다.

예를 들어 오늘 아메리카노 가격이 4,000원인데 한 달 뒤 4,500원으로 변경될 수 있다.

```text
menus.price
→ 현재 판매가격

order_details.sale_price
→ 주문이 발생했던 당시 실제 판매가격
```

과거 주문 내역은 당시 거래 사실을 유지해야 하므로 `sale_price`를 주문상세에 보존한다.

## 오늘의 핵심 정리

> ERD는 단순한 그림이 아니라 실제 데이터베이스 구조의 설계도다. PK는 각 행을 식별하고, FK는 테이블 사이의 관계를 실제 DB에 구현한다. 또한 현재 값과 과거 거래 당시 값을 구분해서 저장해야 데이터의 의미가 보존된다.

## 인프라와 DB의 연결

```text
Ubuntu Server
    ↓
PostgreSQL
    ↓
ai_database_book
    ↓
erd_practice Schema
    ↓
Customers / Menus / Orders / OrderDetails
```

인프라는 **DB가 어디에서 실행되는가**를 다루고, DB 설계는 **그 안에 데이터를 어떤 구조로 저장하는가**를 다룬다.

## 보안 메모

민감한 접속 정보는 학습 기록에 그대로 남기지 않는다.

```text
DB_HOST=***
DB_PASSWORD=***
.env=***
TOKEN=***
```
