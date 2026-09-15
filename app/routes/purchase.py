from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user

from app.models import Product, PurchaseHistory
from app.services.purchase_cycle_service import compute_product_cycles
from app.utils import today_local

purchase_bp = Blueprint("purchase", __name__)


def _build_summary(user_id):
    today = today_local()
    cycles = compute_product_cycles(user_id)
    lead_days = current_app.config.get("REORDER_LEAD_DAYS", 7)

    summary = []
    for product_id, cycle in cycles.items():
        product = Product.query.get(product_id)
        if not product:
            continue

        status = "일반"
        if cycle.has_cycle:
            days_until = cycle.days_until_expected(today)
            if days_until is not None and days_until <= lead_days:
                status = "준비할 시기"

        summary.append(
            {
                "product": product,
                "purchase_count": cycle.purchase_count,
                "last_purchased_at": cycle.last_purchased_at,
                "avg_interval_days": round(cycle.avg_interval_days) if cycle.has_cycle else None,
                "expected_next_date": cycle.expected_next_date,
                "status": status,
            }
        )

    summary.sort(key=lambda s: s["last_purchased_at"], reverse=True)
    return summary


@purchase_bp.route("/purchases")
@login_required
def purchase_history():
    summary = _build_summary(current_user.id)
    raw_history = (
        PurchaseHistory.query.filter_by(user_id=current_user.id)
        .order_by(PurchaseHistory.purchased_at.desc())
        .limit(50)
        .all()
    )
    return render_template("purchase_history.html", summary=summary, raw_history=raw_history)


@purchase_bp.route("/api/purchases")
@login_required
def api_purchase_history():
    history = (
        PurchaseHistory.query.filter_by(user_id=current_user.id)
        .order_by(PurchaseHistory.purchased_at.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": h.id,
                "product_id": h.product_id,
                "product_name": h.product.name if h.product else None,
                "quantity": h.quantity,
                "purchased_at": h.purchased_at.isoformat(),
                "price": h.price,
            }
            for h in history
        ]
    )
