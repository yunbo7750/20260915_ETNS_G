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
