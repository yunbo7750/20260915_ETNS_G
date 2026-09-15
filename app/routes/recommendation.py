from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Recommendation, Cart, CartItem
from app.models.recommendation import TYPE_REORDER, TYPE_LIFE_EVENT, TYPE_PERSONAL
from app.services import recommendation_engine
from app.services.purchase_cycle_service import compute_product_cycles

recommendation_bp = Blueprint("recommendation", __name__)

FILTER_TYPES = {
    "reorder": TYPE_REORDER,
    "life_event": TYPE_LIFE_EVENT,
    "personal": TYPE_PERSONAL,
}


def _get_or_create_cart(user):
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


def _add_recommendation_to_cart(rec, quantity=1):
    cart = _get_or_create_cart(rec.user)
    item = cart.items.filter_by(product_id=rec.product_id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=rec.product_id, quantity=quantity)
        db.session.add(item)

    rec.mark_added_to_cart()
    db.session.commit()
    return item


@recommendation_bp.route("/recommendations")
@login_required
def recommendation_list():
    recommendations = list(recommendation_engine.get_current_batch(current_user))

    active_filter = request.args.get("filter", "all")
    category = request.args.get("category")

    filtered = recommendations
    if active_filter in FILTER_TYPES:
        filtered = [r for r in filtered if r.type == FILTER_TYPES[active_filter]]
    if category:
        filtered = [r for r in filtered if r.product and r.product.category == category]

    page_limit = current_app.config.get("PAGE_MAX_RECOMMENDATIONS", 20)
    filtered = filtered[:page_limit]

    categories = sorted({r.product.category for r in recommendations if r.product})

    return render_template(
        "recommendations.html",
        recommendations=filtered,
        active_filter=active_filter,
        active_category=category,
        categories=categories,
        total_count=len(recommendations),
    )


@recommendation_bp.route("/recommendations/<int:rec_id>")
@login_required
def recommendation_detail(rec_id):
    rec = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first_or_404()
    rec.mark_clicked()
    db.session.commit()

    cycles = compute_product_cycles(current_user.id)
    cycle = cycles.get(rec.product_id)

    return render_template("product_detail.html", product=rec.product, recommendation=rec, cycle=cycle)


@recommendation_bp.route("/recommendations/<int:rec_id>/cart", methods=["POST"])
@login_required
def recommendation_add_to_cart(rec_id):
    rec = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first_or_404()
    quantity = max(1, int(request.form.get("quantity", 1)))
    _add_recommendation_to_cart(rec, quantity)

    flash(f"'{rec.product.name}'을(를) 장바구니에 담았습니다.", "success")
    return redirect(request.referrer or url_for("main.home"))


@recommendation_bp.route("/recommendations/<int:rec_id>/buy-now", methods=["POST"])
@login_required
def recommendation_buy_now(rec_id):
    rec = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first_or_404()
    quantity = max(1, int(request.form.get("quantity", 1)))
    _add_recommendation_to_cart(rec, quantity)

    flash(f"'{rec.product.name}'을(를) 장바구니에 담고 바로 결제를 진행합니다.", "success")
    flash("주문 기능은 프로토타입에서 준비 중입니다.", "info")
    return redirect(url_for("cart.cart_view"))


@recommendation_bp.route("/api/recommendations")
@login_required
def api_recommendation_list():
    recommendations = list(recommendation_engine.get_current_batch(current_user))
    active_filter = request.args.get("filter")
    if active_filter in FILTER_TYPES:
        recommendations = [r for r in recommendations if r.type == FILTER_TYPES[active_filter]]
    return jsonify([r.to_dict() for r in recommendations])


@recommendation_bp.route("/api/recommendations/<int:rec_id>")
@login_required
def api_recommendation_detail(rec_id):
    rec = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first_or_404()
    return jsonify(rec.to_dict())


@recommendation_bp.route("/api/recommendations/<int:rec_id>/click", methods=["POST"])
@login_required
def api_recommendation_click(rec_id):
    rec = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first_or_404()
    rec.mark_clicked()
    db.session.commit()
    return jsonify(rec.to_dict())


@recommendation_bp.route("/api/recommendations/<int:rec_id>/cart", methods=["POST"])
@login_required
def api_recommendation_cart(rec_id):
    rec = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first_or_404()
    _add_recommendation_to_cart(rec)
    return jsonify(rec.to_dict())
