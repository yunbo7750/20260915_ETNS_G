from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Cart, CartItem, Product

cart_bp = Blueprint("cart", __name__)


def _get_or_create_cart(user):
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


@cart_bp.route("/cart")
@login_required
def cart_view():
    cart = _get_or_create_cart(current_user)
    return render_template("cart.html", cart=cart)


@cart_bp.route("/cart/items", methods=["POST"])
@login_required
def cart_add_item():
    product_id = int(request.form.get("product_id"))
    quantity = max(1, int(request.form.get("quantity", 1)))

    product = Product.query.get_or_404(product_id)
    cart = _get_or_create_cart(current_user)

    item = cart.items.filter_by(product_id=product.id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    flash(f"'{product.name}'을(를) 장바구니에 담았습니다.", "success")
    return redirect(request.referrer or url_for("cart.cart_view"))


@cart_bp.route("/cart/buy-now", methods=["POST"])
@login_required
def cart_buy_now():
    product_id = int(request.form.get("product_id"))
    quantity = max(1, int(request.form.get("quantity", 1)))

    product = Product.query.get_or_404(product_id)
    cart = _get_or_create_cart(current_user)

    item = cart.items.filter_by(product_id=product.id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    flash(f"'{product.name}'을(를) 장바구니에 담고 바로 결제를 진행합니다.", "success")
    flash("주문 기능은 프로토타입에서 준비 중입니다.", "info")
    return redirect(url_for("cart.cart_view"))


@cart_bp.route("/cart/items/<int:item_id>", methods=["POST"])
@login_required
def cart_update_item(item_id):
    cart = _get_or_create_cart(current_user)
    item = cart.items.filter_by(id=item_id).first_or_404()

    quantity = int(request.form.get("quantity", item.quantity))
    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = quantity

    db.session.commit()
    return redirect(url_for("cart.cart_view"))


@cart_bp.route("/cart/items/<int:item_id>/delete", methods=["POST"])
@login_required
def cart_delete_item(item_id):
    cart = _get_or_create_cart(current_user)
    item = cart.items.filter_by(id=item_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("상품을 장바구니에서 삭제했습니다.", "info")
    return redirect(url_for("cart.cart_view"))


@cart_bp.route("/cart/checkout", methods=["POST"])
@login_required
def cart_checkout():
    flash("주문 기능은 프로토타입에서 준비 중입니다.", "info")
    return redirect(url_for("cart.cart_view"))


@cart_bp.route("/api/cart")
@login_required
def api_cart_view():
    cart = _get_or_create_cart(current_user)
    return jsonify(
        {
            "items": [item.to_dict() for item in cart.items],
            "total_amount": cart.total_amount,
            "total_quantity": cart.total_quantity,
        }
    )


@cart_bp.route("/api/cart/items", methods=["POST"])
@login_required
def api_cart_add_item():
    data = request.get_json(force=True)
    product = Product.query.get_or_404(int(data["product_id"]))
    quantity = max(1, int(data.get("quantity", 1)))

    cart = _get_or_create_cart(current_user)
    item = cart.items.filter_by(product_id=product.id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@cart_bp.route("/api/cart/items/<int:item_id>", methods=["PUT"])
@login_required
def api_cart_update_item(item_id):
    cart = _get_or_create_cart(current_user)
    item = cart.items.filter_by(id=item_id).first_or_404()
    data = request.get_json(force=True)

    quantity = int(data.get("quantity", item.quantity))
    if quantity <= 0:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"deleted": True})

    item.quantity = quantity
    db.session.commit()
    return jsonify(item.to_dict())


@cart_bp.route("/api/cart/items/<int:item_id>", methods=["DELETE"])
@login_required
def api_cart_delete_item(item_id):
    cart = _get_or_create_cart(current_user)
    item = cart.items.filter_by(id=item_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"deleted": True})
