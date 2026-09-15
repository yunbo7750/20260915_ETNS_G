from datetime import date, timedelta

from app.extensions import db
from app.models import User, Product, PurchaseHistory, Preference, Recommendation
from app.services import recommendation_engine


def _make_user(username="u1"):
    user = User(username=username, name="테스트유저", role="user")
    user.set_password("pw")
    db.session.add(user)
    db.session.flush()
    return user


def test_duplicate_recommendation_from_multiple_engines_is_merged(app_context):
    user = _make_user()
    product = Product(name="신라면", category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()

    # Triggers REORDER: avg interval 45 days, last purchase 42 days ago.
    today = date.today()
    for d in [today - timedelta(days=42 + 45 * i) for i in range(4)]:
        db.session.add(
            PurchaseHistory(user_id=user.id, product_id=product.id, quantity=1, purchased_at=d, price=product.price)
        )

    # Triggers PERSONAL: user likes the product's category.
    db.session.add(Preference(user_id=user.id, target_type="category", category="식품", sentiment="like"))
    db.session.flush()

    results = recommendation_engine.generate_for_user(user, persist=False)
    matching = [r for r in results if r["product_id"] == product.id]

    assert len(matching) == 1
    assert matching[0]["combined_types"] == "REORDER+PERSONAL"


def test_recommendation_score_is_sum_of_engine_scores(app_context):
    user = _make_user()
    product = Product(name="신라면", category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()

    today = date.today()
    for d in [today - timedelta(days=42 + 45 * i) for i in range(4)]:
        db.session.add(
            PurchaseHistory(user_id=user.id, product_id=product.id, quantity=1, purchased_at=d, price=product.price)
        )
    db.session.add(Preference(user_id=user.id, target_type="category", category="식품", sentiment="like"))
    db.session.flush()

    from app.services import reorder_engine, personal_life_engine

    reorder_score = reorder_engine.generate(user)[0]["score"]
    personal_score = personal_life_engine.generate(user)[0]["score"]

    results = recommendation_engine.generate_for_user(user, persist=False)
    combined = next(r for r in results if r["product_id"] == product.id)

    assert combined["score"] == min(reorder_score + personal_score, 100)


def test_recommendations_are_persisted_to_db(app_context):
    user = _make_user()
    product = Product(name="신라면", category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()

    today = date.today()
    for d in [today - timedelta(days=42 + 45 * i) for i in range(4)]:
        db.session.add(
            PurchaseHistory(user_id=user.id, product_id=product.id, quantity=1, purchased_at=d, price=product.price)
        )
    db.session.flush()

    rows = recommendation_engine.generate_for_user(user, persist=True)

    assert len(rows) > 0
    assert Recommendation.query.filter_by(user_id=user.id).count() == len(rows)
