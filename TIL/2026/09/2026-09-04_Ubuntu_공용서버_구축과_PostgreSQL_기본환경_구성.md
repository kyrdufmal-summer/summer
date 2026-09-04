# 2026-09-04 Ubuntu 공용 서버 구축과 PostgreSQL 기본환경 구성

## 오늘 한 일

오늘은 프로젝트에서 여러 조가 안정적으로 개발할 수 있도록 별도의 Ubuntu 공용 서버 PC를 구축했다.

기존처럼 한 대의 개인 개발 PC가 DB 서버 역할까지 함께 담당하면 해당 PC의 전원·이동·네트워크 상태에 따라 다른 개발자들의 작업까지 영향을 받을 수 있다. 이를 줄이기 위해 개발용 PC와 별도로 공용 서버 PC를 준비하고, Ubuntu와 PostgreSQL을 설치해 공용 DB 서버로 사용할 수 있는 기반을 구성했다.

오늘 최종적으로 확인한 상태는 다음과 같다.

- Ubuntu 26.04.1 LTS 정상 부팅
- Ubuntu GUI 환경 설치
- Wi-Fi 연결 및 인터넷 통신 확인
- NetworkManager 설치 및 Wi-Fi 관리 정상화
- Chrome 설치 및 ChatGPT 접속
- 한글 폰트 및 한글 입력 환경 구성
- PostgreSQL 18 설치
- PostgreSQL `main` Cluster `online` 확인
- PostgreSQL 로컬 접속 성공

실제 IP, MAC Address, Wi-Fi 정보, 비밀번호, DB 비밀번호, `.env`, API Key, Token 등 민감정보는 기록하지 않는다.

---

## 1. 왜 개발 PC와 서버 PC를 분리해야 하는가?

개인 개발환경에서는 한 대의 PC에서 VS Code, Django, PostgreSQL을 모두 실행해도 된다.

```text
개발자 PC
├─ VS Code
├─ Django
├─ PostgreSQL
└─ Browser
```

하지만 여러 명이 하나의 DB를 공유하는 프로젝트에서는 한 사람의 PC가 DB 서버까지 담당하면 해당 PC가 꺼졌을 때 다른 사람도 DB를 사용할 수 없다.

```text
개발자 A PC
└─ PostgreSQL
     ↑
개발자 B
개발자 C
개발자 D
```

이를 분리하면 다음과 같은 구조가 된다.

```text
[개발자 PC 1] ─┐
[개발자 PC 2] ─┤
[개발자 PC 3] ─┼──→ [공용 Ubuntu 서버]
[개발자 PC 4] ─┘          │
                           └─ PostgreSQL
```

정리하면,

```text
개발 PC = 개발하는 컴퓨터
서버 PC = 다른 컴퓨터들에게 지속적으로 서비스를 제공하는 컴퓨터
```

이라고 이해할 수 있다.

---

## 2. 서버란 무엇인가?

서버는 특별한 모양의 컴퓨터를 의미하는 것이 아니라, 다른 컴퓨터에 어떤 기능을 제공하는 역할을 하는 컴퓨터 또는 프로그램을 의미한다.

오늘 구축한 PC는 PostgreSQL을 실행하고 다른 개발자들의 Django 프로젝트가 접속하게 될 예정이므로 DB 서버 역할을 하게 된다.

```text
Django Client
    ↓
Ubuntu Server
    ↓
PostgreSQL
    ↓
Database
```

---

## 3. 왜 Ubuntu를 사용하는가?

Ubuntu는 Linux 운영체제 중 하나다. 서버 환경에서는 Windows보다 Linux 계열 운영체제가 많이 사용된다.

```text
Hardware
   ↓
Ubuntu
   ↓
PostgreSQL
   ↓
Project Database
```

Ubuntu는 하드웨어와 프로그램 사이에서 CPU, Memory, Disk, Network 같은 자원을 관리하고 PostgreSQL 같은 서버 프로그램이 실행될 수 있는 환경을 제공한다.

서버 환경에서 Ubuntu를 많이 사용하는 이유는 다음과 같다.

- 서버 운영에 적합함
- 원격 관리가 쉬움
- PostgreSQL, Python, Git 등 개발도구 설치가 편리함
- 명령어 기반 자동화가 쉬움
- 실제 Linux 서버 환경과 유사하게 학습 가능함

---

## 4. Ubuntu CLI와 GUI

처음 Ubuntu를 부팅했을 때는 다음과 같은 터미널 화면만 보였다.

```text
kant@kant:~$
```

이것은 CLI(Command Line Interface) 환경이다.

### CLI

명령어를 직접 입력해 시스템을 조작한다.

```bash
ip addr
```

### GUI

Windows처럼 창, 아이콘, 마우스를 사용하는 방식이다.

서버 전용 환경이라면 GUI가 없어도 되지만, 이번 프로젝트에서는 여러 조원이 서버 PC를 직접 확인하고 관리해야 하므로 사용 편의를 위해 GUI도 함께 구성했다.

---

## 5. 오늘 사용한 Linux 기본 명령어

### 네트워크 정보 확인

```bash
ip addr
```

현재 PC의 네트워크 인터페이스와 IP 정보를 확인한다.

### 네트워크 장치 상태 확인

```bash
ip link
```

Ethernet, Wi-Fi 등의 인터페이스가 활성화되어 있는지 확인한다.

### 하드웨어 확인

```bash
lspci
```

PC에 장착된 PCI 장치를 확인한다. 오늘은 이 명령으로 Intel Wi-Fi 장치가 존재하는 것을 확인했다.

### 인터넷 연결 확인

```bash
ping -c 3 google.com
```

외부 네트워크까지 정상적으로 통신되는지 확인한다.

### Ubuntu 패키지 목록 갱신

```bash
sudo apt update
```

설치 가능한 패키지들의 최신 목록을 가져온다.

---

## 6. `sudo`의 역할

Ubuntu에서 시스템 설정을 변경하거나 프로그램을 설치할 때 `sudo`를 사용한다.

```bash
sudo apt install ...
```

`sudo`는 일반 사용자에게 일시적으로 관리자 권한을 부여한다. Windows의 "관리자 권한으로 실행"과 비슷하다.

비밀번호를 입력할 때 화면에 `****`가 표시되지 않아도 정상이다.

---

## 7. Wi-Fi 연결 과정과 NetworkManager

처음에는 Wi-Fi 하드웨어와 드라이버는 존재했지만 NetworkManager가 Wi-Fi 인터페이스를 관리하지 않는 `unmanaged` 상태였다.

NetworkManager는 Ubuntu에서 Wi-Fi와 Ethernet 등의 네트워크 연결을 관리하는 프로그램이다.

```text
NetworkManager
      │
      ├─ Ethernet
      └─ Wi-Fi
```

`nmcli`는 NetworkManager를 터미널에서 조작하는 도구다.

```bash
nmcli device status
```

Wi-Fi 인터페이스를 관리 대상으로 변경한 뒤 주변 Wi-Fi 검색과 연결이 정상적으로 가능해졌다.

---

## 8. 휴대폰 USB 테더링을 사용한 이유

초기에는 서버 PC가 인터넷에 연결되지 않아 필요한 패키지를 설치하기 어려웠다. 그래서 휴대폰 USB 테더링을 임시 인터넷 연결 수단으로 사용했다.

```text
휴대폰
  ↓ USB
Ubuntu Server
  ↓
Internet
```

인터넷 연결을 확보한 뒤 NetworkManager 등 필요한 프로그램을 설치하고 최종적으로 서버 자체 Wi-Fi로 전환했다.

---

## 9. Chrome과 ChatGPT 환경 구성

GUI 설치 후 브라우저를 통해 서버 PC에서도 ChatGPT를 사용할 수 있도록 구성했다.

Firefox도 설치되어 있었지만 한글 폰트 표시 문제를 겪었고, 이후 Chrome을 추가 설치해 사용 환경을 구성했다.

서버 PC에서 바로 ChatGPT에 접속할 수 있으므로 서버 설정 중 발생하는 오류 메시지나 명령어를 즉시 확인할 수 있다.

---

## 10. 한글 폰트와 한글 입력기는 다르다

한글을 화면에 표시하는 것과 한글을 입력하는 것은 서로 다른 기능이다.

### 한글 폰트

한글 글자를 화면에 보여주는 역할을 한다.

확인한 폰트:

```text
Noto Sans CJK KR
```

### 한글 입력기

키보드 입력을 실제 한글 문자로 조합한다.

```text
ㅎ + ㅏ + ㄴ → 한
```

오늘은 `ibus-hangul`을 설치하고 `Korean (Hangul)` Input Source를 추가했다.

```text
English (US)
Korean (Hangul)
```

입력 Source 전환은 다음 단축키를 사용할 수 있다.

```text
Super + Space
```

`Super`는 Windows 로고 키다.

---

## 11. Ubuntu Terminal의 복사/붙여넣기

일반 프로그램과 터미널은 단축키가 다르다.

일반 프로그램:

```text
복사: Ctrl + C
붙여넣기: Ctrl + V
```

터미널:

```text
복사: Ctrl + Shift + C
붙여넣기: Ctrl + Shift + V
```

터미널에서 `Ctrl + C`는 복사가 아니라 현재 실행 중인 명령을 중단하는 기능이다.

---

## 12. PostgreSQL 설치

오늘 공용 서버에 PostgreSQL 18을 설치했다.

PostgreSQL은 Django 프로젝트의 데이터를 저장하고 조회할 DBMS다.

```text
Django
  ↓ SQL
PostgreSQL
  ↓
Database
```

---

## 13. PostgreSQL Cluster

다음 명령으로 PostgreSQL Cluster 상태를 확인했다.

```bash
pg_lsclusters
```

확인 결과 PostgreSQL 18의 `main` Cluster가 `online` 상태였다.

```text
PostgreSQL 18
    ↓
Cluster: main
    ↓
Databases
```

Cluster는 PostgreSQL 서버가 실제 데이터를 관리하는 실행 단위로 이해할 수 있다.

---

## 14. Port 5432의 의미

PostgreSQL 기본 Port는 일반적으로 5432다.

IP가 컴퓨터를 찾는 주소라면 Port는 그 컴퓨터 안에서 어떤 프로그램으로 연결할지 구분하는 번호라고 생각할 수 있다.

```text
Server IP
   +
Port 5432
   ↓
PostgreSQL
```

실제 서버 IP는 문서에 기록하지 않고 `***`로 관리한다.

---

## 15. PostgreSQL 로컬 접속 테스트

설치만 완료했다고 DB가 정상 동작한다고 판단할 수 없으므로 실제 접속 테스트를 진행했다.

```bash
sudo -u postgres psql
```

정상 접속 시 다음 프롬프트가 나타난다.

```text
postgres=#
```

오늘 실제로 이 단계까지 정상 확인했다.

```text
PostgreSQL 설치
      ↓
Cluster online
      ↓
Local Connection 성공
```

---

## 16. 로컬 접속과 외부 접속의 차이

오늘 확인한 것은 로컬 접속이다.

```text
Ubuntu Server
└─ PostgreSQL
     ↑
같은 PC에서 접속
```

최종적으로 필요한 구조는 다음과 같다.

```text
조원 PC
   ↓ Network
공용 Ubuntu Server
   ↓
PostgreSQL
```

이를 위해서는 외부 접속 관련 추가 설정이 필요하다.

---

## 17. 월요일 진행할 PostgreSQL 외부 접속 설정

### 프로젝트용 DB 생성

Django 프로젝트에서 사용할 별도 Database를 생성해야 한다.

### DB Role/User 생성

모든 사용자가 `postgres` 관리자 계정을 직접 사용하는 대신 프로젝트용 Role을 생성하고 필요한 권한만 부여하는 것이 좋다.

### `listen_addresses`

PostgreSQL이 외부 네트워크의 접속 요청을 받을지 결정한다.

### `pg_hba.conf`

어떤 사용자와 네트워크가 어떤 DB에 접속할 수 있는지를 결정하는 접근 제어 설정이다.

```text
접속 요청
  ↓
pg_hba.conf
  ↓
허용 / 거부
```

### Firewall

Ubuntu 자체 방화벽에서도 PostgreSQL Port에 대한 접근 가능 여부를 확인해야 한다.

---

## 18. Django와 공용 PostgreSQL 연결 구조

최종 목표는 각 조의 프로젝트가 동일한 공용 DB 서버를 바라보는 구조다.

```text
1조 Django ─┐
2조 Django ─┤
3조 Django ─┼──→ 공용 PostgreSQL Server
4조 Django ─┘
```

Django의 DB 설정값은 환경변수로 관리하며 실제 값은 Git에 올리지 않는다.

```text
POSTGRES_HOST=***
POSTGRES_PORT=***
POSTGRES_DB=***
POSTGRES_USER=***
POSTGRES_PASSWORD=***
```

---

## 19. `.env`를 Git에 올리면 안 되는 이유

`.env`에는 DB 비밀번호, Secret Key, API Token 등 민감정보가 들어갈 수 있다.

```text
POSTGRES_PASSWORD=***
API_KEY=***
SECRET_KEY=***
TOKEN=***
```

실제 값은 Git History에 남기지 않고 `.env.example`에는 변수명과 예시 형식만 공유하는 것이 안전하다.

---

## 20. 공용 DB 서버의 핵심 목적

오늘 작업의 핵심은 PostgreSQL 설치 자체보다 다음 구조를 만드는 데 있다.

```text
특정 개인 PC의 상태와 프로젝트 DB 상태를 분리한다.
```

개발자의 PC가 꺼지거나 이동해도 공용 DB 서버가 유지되면 다른 조는 계속 개발할 수 있다.

```text
개발자 PC OFF
      ↓
공용 DB Server는 계속 ON
      ↓
다른 조 개발 계속 가능
```

---

## 21. 공용 서버 한 대만으로 완전히 안전한 것은 아니다

특정 개인 PC 의존성은 줄었지만 공용 서버 자체에 장애가 생기면 다시 전체 DB 사용이 어려워질 수 있다.

따라서 공용 서버와 별개로 백업 정책과 복구 절차가 필요하다.

```text
공용 DB Server
      │
      ├─ 운영 DB
      └─ Backup
```

초기 단계에서 서버 PC 두 대를 반드시 동시에 운영할 필요는 없지만 최소한 다음은 필요하다.

```text
공용 DB 서버 1대
+
정기적인 DB Backup
+
복구 절차
```

향후 필요하면 Standby/Backup Server 구조까지 고려할 수 있다.

---

## 22. 월요일 작업 순서

```text
기존 DB 상태 확인
      ↓
Schema / Data 확인
      ↓
Backup
      ↓
새 공용 서버 DB 생성
      ↓
DB Role / 권한 설정
      ↓
필요한 Schema / Data 이관
      ↓
외부 접속 설정
      ↓
pg_hba.conf 설정
      ↓
Port / Firewall 확인
      ↓
조원 PC 원격 접속 Cross Check
      ↓
Django .env 변경
      ↓
Migration Test
      ↓
실제 조회 / 저장 Test
      ↓
Backup / Restore Test
```

기존 DB를 확인하지 않고 새 서버에 Migration부터 적용하면 Schema 차이나 기존 데이터와의 충돌 가능성이 있으므로 기존 상태 확인과 Backup을 먼저 진행해야 한다.

---

## 23. 오늘 서버 상태

### GREEN

- Ubuntu 정상 설치 및 부팅
- Ubuntu GUI
- Wi-Fi
- Internet
- NetworkManager
- Chrome
- ChatGPT 접속
- 한글 폰트
- 한글 입력기
- PostgreSQL 18
- PostgreSQL main Cluster online
- PostgreSQL local connection

### PENDING

- 프로젝트용 Database
- 프로젝트용 DB Role/User
- DB 권한
- 기존 DB Backup
- Schema/Data Migration
- 외부 접속
- `pg_hba.conf`
- Firewall
- 공용 서버 IP 운영 기준
- 조원 PC Cross Check
- Django 연결
- Migration 검증
- 실제 CRUD Test
- Backup/Restore Test

---

## 24. 오늘 배운 Ubuntu 기본 단축키와 명령어

터미널 열기:

```text
Ctrl + Alt + T
```

입력 Source 전환:

```text
Super + Space
```

일반 프로그램 복사/붙여넣기:

```text
Ctrl + C
Ctrl + V
```

터미널 복사/붙여넣기:

```text
Ctrl + Shift + C
Ctrl + Shift + V
```

실행 중인 터미널 명령 중단:

```text
Ctrl + C
```

현재 사용자 확인:

```bash
whoami
```

현재 경로 확인:

```bash
pwd
```

파일/폴더 확인:

```bash
ls
```

화면 정리:

```bash
clear
```

네트워크 확인:

```bash
ip addr
```

PostgreSQL Cluster 확인:

```bash
pg_lsclusters
```

PostgreSQL `psql` 종료:

```text
\q
```

Ubuntu 재부팅:

```bash
sudo reboot
```

Ubuntu 종료:

```bash
sudo poweroff
```

---

## 25. 오늘의 핵심 이해

오늘 가장 크게 이해한 것은 서버 구축이 단순히 프로그램 하나를 설치하는 작업이 아니라는 점이다.

```text
Hardware
   ↓
Operating System (Ubuntu)
   ↓
Network
   ↓
Server IP / Port
   ↓
PostgreSQL
   ↓
Database / Role / Permission
   ↓
Django
   ↓
각 조의 개발환경
```

중간 단계 중 하나라도 문제가 생기면 개발자 입장에서는 단순한 `DB Connection Error`로 보일 수 있다.

따라서 장애가 발생하면 다음 순서로 확인하는 것이 중요하다.

```text
서버가 켜져 있는가?
↓
네트워크가 연결되어 있는가?
↓
IP가 정상인가?
↓
PostgreSQL이 실행 중인가?
↓
Port가 정상인가?
↓
접근 권한이 있는가?
↓
DB 접속정보가 맞는가?
↓
Django 설정이 맞는가?
```

---

## 오늘의 한 줄 정리

오늘은 단순히 Ubuntu와 PostgreSQL을 설치한 것이 아니라, **특정 개인 PC에 의존하지 않고 여러 조가 안정적으로 개발할 수 있는 공용 DB 서버의 기반을 구축하고 서버·네트워크·DB가 어떻게 연결되는지 실제로 확인한 날이었다.**
