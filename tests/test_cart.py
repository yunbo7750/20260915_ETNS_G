from app.extensions import db
from app.models import User, Product, Cart, CartItem


def _make_user_with_cart(username="u1"):
    user = User(username=username, name="테스트유저", role="user")
    user.set_password("pw")
    db.session.add(user)
    db.session.flush()
    cart = Cart(user_id=user.id)
    db.session.add(cart)
    db.session.flush()
    return user, cart


def test_add_item_to_cart(app_context):
    _, cart = _make_user_with_cart()
    product = Product(name="신라면", category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    db.session.add(item)
    db.session.flush()

    assert cart.items.count() == 1
    assert cart.total_quantity == 2
    assert cart.total_amount == 8000


def test_update_item_quantity(app_context):
    _, cart = _make_user_with_cart()
    product = Product(name="신라면", category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()
    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    db.session.add(item)
    db.session.flush()

    item.quantity = 5
    db.session.flush()

    assert cart.total_quantity == 5
    assert cart.total_amount == 20000


def test_delete_item_from_cart(app_context):
    _, cart = _make_user_with_cart()
    product = Product(name="신라면", category="식품", price=4000, active=True)
    db.session.add(product)
    db.session.flush()
    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    db.session.add(item)
    db.session.flush()

    db.session.delete(item)
    db.session.flush()

    assert cart.items.count() == 0
    assert cart.total_amount == 0


def test_total_amount_across_multiple_items(app_context):
    _, cart = _make_user_with_cart()
    p1 = Product(name="신라면", category="식품", price=4000, active=True)
    p2 = Product(name="샴푸", category="욕실용품", price=7000, active=True)
    db.session.add_all([p1, p2])
    db.session.flush()

    db.session.add(CartItem(cart_id=cart.id, product_id=p1.id, quantity=2))
    db.session.add(CartItem(cart_id=cart.id, product_id=p2.id, quantity=1))
    db.session.flush()

    assert cart.total_amount == 4000 * 2 + 7000
