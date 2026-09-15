from datetime import date, timedelta

from app.extensions import db
from app.models import User, Product, PurchaseHistory
from app.services import reorder_engine


def _make_user(username="u1"):
    user = User(username=username, name="테스트유저", role="user")
    user.set_password("pw")
    db.session.add(user)
    db.session.flush()
    return user


def _make_product(name="신라면"):
    product = Product(name=name, category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()
    return product


def _add_purchases(user, product, last_ago_days, interval_days, count):
    today = date.today()
    last_date = today - timedelta(days=last_ago_days)
    dates = [last_date - timedelta(days=interval_days * i) for i in range(count)]
    for d in dates:
        db.session.add(
            PurchaseHistory(user_id=user.id, product_id=product.id, quantity=1, purchased_at=d, price=product.price)
        )
    db.session.flush()


def test_reorder_recommended_when_purchase_cycle_is_due(app_context):
    user = _make_user()
    product = _make_product()
    # avg interval 45 days, last purchased 42 days ago -> expected next date is
    # 3 days from now, well within the default 7-day lead window.
    _add_purchases(user, product, last_ago_days=42, interval_days=45, count=4)

    candidates = reorder_engine.generate(user)

    assert any(c["product_id"] == product.id for c in candidates)


def test_reorder_not_recommended_when_recently_purchased(app_context):
    user = _make_user()
    product = _make_product()
    # avg interval 45 days, last purchased only 5 days ago -> next purchase is
    # 40 days away, far outside the lead window. Must not be recommended.
    _add_purchases(user, product, last_ago_days=5, interval_days=45, count=4)

    candidates = reorder_engine.generate(user)

    assert not any(c["product_id"] == product.id for c in candidates)


def test_reorder_requires_minimum_purchase_count(app_context):
    user = _make_user()
    product = _make_product()
    # Only one purchase ever - no cycle can be computed yet.
    _add_purchases(user, product, last_ago_days=42, interval_days=45, count=1)

    candidates = reorder_engine.generate(user)

    assert candidates == []
