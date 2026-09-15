# ETNERS LIFE (가칭)

> 찾아서 사는 쇼핑몰에서, 필요할 때 먼저 알려주는 쇼핑몰로.

해외 주재원/파견 직원이 한국 생활용품을 "직접 찾아서" 사는 대신, 구매 주기·생활
일정·개인 프로필을 분석해 **쇼핑몰이 먼저 필요한 상품을 제안**하는 선제적 구매
제안 서비스의 MVP입니다.

서비스명(ETNERS LIFE)은 `config.py`의 `SERVICE_NAME` 값으로만 관리되며 코드
어디에도 하드코딩되어 있지 않아, 환경변수 `SERVICE_NAME`만 바꾸면 즉시 다른
이름으로 서비스할 수 있습니다.

## 서비스 컨셉

일반적인 "상품 검색 → 상품 선택" 흐름이 아니라

```
상황 발생 → 필요한 상품 자동 제안(+이유) → 확인 → 장바구니 → 구매
```

의 흐름을 만듭니다. 모든 추천 카드에는 **왜 이 상품을 지금 추천하는지**가
사람이 읽을 수 있는 문장으로 함께 표시됩니다.

## 주요 기능

- 홈 화면: "다시 구매할 시기 / 일정에 맞춰 준비 / 나에게 맞는 추천" 3분할 추천
- 추천 전체보기 (유형/카테고리 필터)
- 상품 상세 (추천 이유 + 구매 주기 정보)
- 구매 이력 및 "다음 구매 예상" 화면
- 생활 일정(캘린더) 등록/삭제 — 등록 즉시 관련 추천 재계산
- 프로필: 가족 구성, 선호/비선호 카테고리·상품 관리
- 온보딩 퀴즈 (건너뛰기 가능)
- 장바구니 (담기/수량변경/삭제, 주문하기는 프로토타입 안내만 표시)
- 알림 센터 (새 추천/일정 알림)
- 관리자 대시보드 (사용자/상품/구매/추천 현황, 추천 유형별 클릭률)

## 추천 엔진 구조

```
RecommendationEngine (app/services/recommendation_engine.py)
    ├── ReorderEngine        (구매 주기 기반 재구매 추천)
    ├── LifeCalendarEngine   (등록된 일정 기반 추천)
    └── PersonalLifeEngine   (가족 구성·선호도·구매 카테고리 기반 개인화 추천)
        ↓
    후보 병합 (동일 상품이 여러 엔진에서 나오면 점수 합산 + 이유 결합)
        ↓
    점수/이유 확정 → Recommendation 테이블에 저장 → Notification 생성
```

세 엔진은 각각 `generate(user) -> list[dict]` 형태의 순수 함수로 분리되어
있어, 이후 규칙 기반 엔진을 AI/ML 기반 엔진으로 교체하더라도
`RecommendationEngine`과 그 위의 라우트/템플릿은 전혀 수정할 필요가 없습니다.

### 1. REORDER ENGINE (`app/services/reorder_engine.py`)

사용자의 상품별 구매 이력(`app/services/purchase_cycle_service.py`)으로부터
평균 구매 주기와 예상 다음 구매일을 계산하고, 그 날짜가
`REORDER_LEAD_DAYS`(기본 7일) 이내로 다가오면 추천합니다. 최근에 막 구매한
상품은 다음 예상일이 멀기 때문에 자동으로 과소비 추천이 방지됩니다.

### 2. LIFE CALENDAR ENGINE (`app/services/life_calendar_engine.py`)

사용자가 등록한 일정(`CalendarEvent`) 중 `EVENT_RECOMMENDATION_DAYS`의 최대값
(기본 30일) 이내로 다가온 일정에 대해, `EVENT_TYPE_PRODUCT_TAGS` 설정에 따라
관련 카테고리/태그 상품을 추천합니다.

### 3. PERSONAL LIFE ENGINE (`app/services/personal_life_engine.py`)

가족 구성(자녀 유무), 선호/비선호 카테고리·상품, 카테고리별 구매 빈도를
종합해 점수를 매깁니다. 비선호로 등록한 카테고리/상품은 추천에서 제외됩니다.

### 점수·가중치

모든 가중치는 `config.py`의 `SCORE_*` 값으로 관리되며 코드에 흩어져
하드코딩되어 있지 않습니다. 여러 엔진에서 같은 상품이 추천되면 점수를
합산(최대 100점)하고, 추천 이유 문장도 이어붙여 하나의 추천으로 통합합니다.

## 기술 스택

- Backend: Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Login
- Frontend: Jinja2, Bootstrap 5 (CDN)
- DB: SQLite (`instance/etners_life.db`), SQLAlchemy ORM
- Test: pytest

## 설치 방법

```bash
cd etners-life
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
```

## 실행 방법

```bash
python seed.py          # DB 초기화 + 샘플 데이터 생성 (재실행 시 전체 초기화)
python app.py            # http://127.0.0.1:5000 에서 실행
```

또는 Flask CLI로 테이블만 생성하려면:

```bash
flask --app app.py init-db
```

## 테스트 방법

```bash
pytest tests/ -v
```

`tests/test_reorder.py`, `test_calendar.py`, `test_personalization.py`,
`test_recommendation.py`, `test_cart.py` 각각 재구매 판단, 일정 기반 추천,
개인화 점수, 중복 추천 병합/점수 합산, 장바구니 동작을 검증합니다.

## 계정 정보

| 구분 | 아이디 | 비밀번호 |
|---|---|---|
| 관리자 | `admin` | `admin1234` |
| 사용자 | `user01` ~ `user05` | `user1234` |

5명의 사용자는 서로 다른 구매 이력·가족 구성·선호도·일정을 가지고 있어,
로그인 계정에 따라 홈 화면 추천 결과가 실제로 다르게 나타납니다.

## 프로젝트 구조

```
etners-life/
├── app.py                  # 엔트리포인트, `flask init-db` CLI
├── config.py                # 서비스명, 점수 가중치, 추천 규칙 설정
├── seed.py                   # 샘플 데이터 생성 스크립트
├── requirements.txt
├── instance/                 # SQLite DB 파일 위치
├── app/
│   ├── __init__.py           # Flask 앱 팩토리
│   ├── extensions.py          # db, login_manager
│   ├── utils.py                # 시간대(Asia/Seoul) 유틸
│   ├── models/                  # User, FamilyMember, Preference, Product,
│   │                            PurchaseHistory, CalendarEvent,
│   │                            Recommendation, Notification, Cart/CartItem
│   ├── routes/                  # auth, main, recommendation, product,
│   │                            calendar, purchase, cart, admin
│   ├── services/                 # 3대 추천 엔진 + 오케스트레이터 +
│   │                            구매주기 계산 + 알림 생성
│   ├── templates/                # Jinja2 템플릿 (Bootstrap 5)
│   └── static/                    # css/js
└── tests/
```

## 향후 AI 추천 엔진으로 확장하는 방법

현재 `RecommendationEngine`은 세 개의 규칙 기반 엔진(`reorder_engine`,
`life_calendar_engine`, `personal_life_engine`)을 호출해 후보를 모읍니다.
각 엔진은 `generate(user) -> list[{product_id, type, score, reason,
expected_date}]` 라는 동일한 인터페이스만 지키면 되므로:

1. 예를 들어 `ai_recommendation_engine.py`를 새로 만들어 학습된 모델/임베딩
   유사도 등으로 후보를 생성하도록 구현합니다.
2. `recommendation_engine.py`의 `_CANDIDATE_ENGINES` 리스트에 이 모듈을
   추가(또는 규칙 기반 엔진과 교체)합니다.
3. `Recommendation`/`RecommendationLog` 성격의 테이블에는 이미 클릭·장바구니
   전환 데이터가 쌓이고 있으므로, 이를 학습 데이터로 바로 활용할 수 있습니다.

라우트, 템플릿, 관리자 대시보드는 추천이 어떤 엔진에서 나왔는지 알 필요가
없도록 설계되어 있어 위 변경만으로 하이브리드(Rule + AI) 추천으로 자연스럽게
전환할 수 있습니다.
