from app.extensions import db
from app.models import User, FamilyMember, Preference, Product
from app.services import personal_life_engine


def _make_user(username="u1"):
    user = User(username=username, name="테스트유저", role="user")
    user.set_password("pw")
    db.session.add(user)
    db.session.flush()
    return user


def test_child_presence_boosts_child_products(app_context):
    user = _make_user()
    db.session.add(FamilyMember(user_id=user.id, relation="자녀", birth_date=None))
    child_product = Product(name="어린이 도서", category="어린이도서", price=10000, active=True)
    other_product = Product(name="세탁세제", category="세제", price=9000, active=True)
    db.session.add_all([child_product, other_product])
    db.session.flush()

    candidates = personal_life_engine.generate(user)
    candidate_ids = {c["product_id"] for c in candidates}

    assert child_product.id in candidate_ids
    assert other_product.id not in candidate_ids


def test_preferred_category_boosts_score(app_context):
    user = _make_user()
    coffee_product = Product(name="원두커피", category="커피", price=12000, active=True)
    book_product = Product(name="소설책", category="도서", price=15000, active=True)
    db.session.add_all([coffee_product, book_product])
    db.session.flush()
    db.session.add(Preference(user_id=user.id, target_type="category", category="커피", sentiment="like"))
    db.session.flush()

    candidates = personal_life_engine.generate(user)
    candidate_ids = {c["product_id"] for c in candidates}

    assert coffee_product.id in candidate_ids
    assert book_product.id not in candidate_ids


def test_disliked_category_is_excluded(app_context):
    user = _make_user()
    coffee_product = Product(name="원두커피", category="커피", price=12000, active=True)
    db.session.add(coffee_product)
    db.session.flush()
    db.session.add(Preference(user_id=user.id, target_type="category", category="커피", sentiment="like"))
    db.session.add(Preference(user_id=user.id, target_type="category", category="커피", sentiment="dislike"))
    db.session.flush()

    candidates = personal_life_engine.generate(user)

    # An explicit dislike on the category excludes the product even if a
    # like entry also exists (dislikes always win).
    assert coffee_product.id not in {c["product_id"] for c in candidates}
