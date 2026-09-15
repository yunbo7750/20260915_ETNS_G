from datetime import date, timedelta

from app.extensions import db
from app.models import User, Product, CalendarEvent
from app.services import life_calendar_engine


def _make_user(username="u1"):
    user = User(username=username, name="테스트유저", role="user")
    user.set_password("pw")
    db.session.add(user)
    db.session.flush()
    return user


def _make_product(name="어린이 동화책", category="어린이도서", tags="어린이도서"):
    product = Product(name=name, category=category, price=10000, tags=tags, active=True)
    db.session.add(product)
    db.session.flush()
    return product


def test_event_within_lookahead_is_recommended(app_context):
    user = _make_user()
    _make_product()
    db.session.add(
        CalendarEvent(
            user_id=user.id, title="자녀 생일", event_type="자녀생일",
            event_date=date.today() + timedelta(days=14),
        )
    )
    db.session.flush()

    candidates = life_calendar_engine.generate(user)

    assert len(candidates) > 0
    assert all(c["type"] == "LIFE_EVENT" for c in candidates)


def test_event_far_in_future_is_not_recommended(app_context):
    user = _make_user()
    _make_product()
    db.session.add(
        CalendarEvent(
            user_id=user.id, title="먼 미래 행사", event_type="자녀생일",
            event_date=date.today() + timedelta(days=60),
        )
    )
    db.session.flush()

    candidates = life_calendar_engine.generate(user)

    assert candidates == []


def test_event_keyword_matches_unrelated_product(app_context):
    user = _make_user()
    vitamin_product = _make_product(
        name="어린이 비타민 젤리", category="과자", tags="간식,건강,비타민"
    )
    unrelated_product = _make_product(name="베스트셀러 소설", category="도서", tags="도서")
    db.session.add(
        CalendarEvent(
            user_id=user.id, title="아이 건강검진", event_type="기타",
            event_date=date.today() + timedelta(days=5),
            keywords="비타민, 건강",
        )
    )
    db.session.flush()

    candidates = life_calendar_engine.generate(user)
    candidate_ids = {c["product_id"] for c in candidates}

    assert vitamin_product.id in candidate_ids
    assert unrelated_product.id not in candidate_ids
    matched = next(c for c in candidates if c["product_id"] == vitamin_product.id)
    assert "키워드" in matched["reason"]
