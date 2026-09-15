from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.models import Product, Recommendation
from app.services import recommendation_engine
from app.services.purchase_cycle_service import compute_product_cycles

product_bp = Blueprint("product", __name__)


@product_bp.route("/products")
@login_required
def product_list():
    category = request.args.get("category")
    query = Product.query.filter_by(active=True)
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.name.asc()).all()

    categories = sorted({p.category for p in Product.query.filter_by(active=True).all()})
    return render_template(
        "products.html", products=products, categories=categories, active_category=category
    )


@product_bp.route("/products/<int:product_id>")
@login_required
def product_detail(product_id):
    product = Product.query.filter_by(id=product_id, active=True).first_or_404()

    recommendation = (
        Recommendation.query.filter_by(user_id=current_user.id, product_id=product_id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    cycles = compute_product_cycles(current_user.id)
    cycle = cycles.get(product_id)

    return render_template(
        "product_detail.html", product=product, recommendation=recommendation, cycle=cycle
    )


@product_bp.route("/api/products")
@login_required
def api_product_list():
    category = request.args.get("category")
    query = Product.query.filter_by(active=True)
    if category:
        query = query.filter_by(category=category)
    return jsonify([p.to_dict() for p in query.all()])


@product_bp.route("/api/products/<int:product_id>")
@login_required
def api_product_detail(product_id):
    product = Product.query.filter_by(id=product_id, active=True).first_or_404()
    return jsonify(product.to_dict())
