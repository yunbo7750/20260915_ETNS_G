from datetime import datetime, time

from flask import Blueprint, render_template
from flask_login import login_required

from app.models import User, Product, PurchaseHistory, Recommendation
from app.models.recommendation import TYPE_REORDER, TYPE_LIFE_EVENT, TYPE_PERSONAL
from app.routes.decorators import admin_required
from app.utils import today_local

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALL_TYPES = [TYPE_REORDER, TYPE_LIFE_EVENT, TYPE_PERSONAL]
TYPE_LABELS = {
    TYPE_REORDER: "재구매(REORDER)",
    TYPE_LIFE_EVENT: "생활일정(LIFE_EVENT)",
    TYPE_PERSONAL: "개인화(PERSONAL)",
}


def _type_breakdown():
    breakdown = []
    for t in ALL_TYPES:
        query = Recommendation.query.filter_by(type=t)
        generated = query.count()
        clicked = query.filter_by(is_clicked=True).count()
        added_to_cart = query.filter_by(is_added_to_cart=True).count()
        ctr = round((clicked / generated) * 100, 1) if generated else 0.0
        breakdown.append(
            {
                "type": t,
                "label": TYPE_LABELS[t],
                "generated": generated,
                "clicked": clicked,
                "added_to_cart": added_to_cart,
                "ctr": ctr,
            }
        )
    return breakdown


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    today = today_local()
    today_start = datetime.combine(today, time.min)

    total_recommendations = Recommendation.query.count()
    today_recommendations = Recommendation.query.filter(
        Recommendation.created_at >= today_start
    ).count()
    total_clicks = Recommendation.query.filter_by(is_clicked=True).count()
    total_cart_adds = Recommendation.query.filter_by(is_added_to_cart=True).count()
    overall_ctr = (
        round((total_clicks / total_recommendations) * 100, 1) if total_recommendations else 0.0
    )

    stats = {
        "user_count": User.query.filter_by(role="user").count(),
        "product_count": Product.query.count(),
        "purchase_count": PurchaseHistory.query.count(),
        "total_recommendations": total_recommendations,
        "today_recommendations": today_recommendations,
        "total_clicks": total_clicks,
        "total_cart_adds": total_cart_adds,
        "overall_ctr": overall_ctr,
    }

    return render_template("admin/dashboard.html", stats=stats, breakdown=_type_breakdown())
