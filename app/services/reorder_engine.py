"""ENGINE 1 - REORDER ENGINE

Recommends products the user is likely due to repurchase, based on their
personal purchase cycle (average interval between purchases).
"""
from flask import current_app

from app.models import Product
from app.models.recommendation import TYPE_REORDER
from app.services.purchase_cycle_service import compute_product_cycles
from app.utils import today_local


def generate(user) -> list[dict]:
    """Returns a list of candidate recommendation dicts for this user."""
    today = today_local()
    lead_days = current_app.config.get("REORDER_LEAD_DAYS", 7)
    base_score = current_app.config.get("SCORE_REORDER", 40)

    cycles = compute_product_cycles(user.id)
    candidates = []

    for product_id, cycle in cycles.items():
        if not cycle.has_cycle:
            continue

        days_until = cycle.days_until_expected(today)
        if days_until is None or days_until > lead_days:
            continue

        product = Product.query.get(product_id)
        if not product or not product.active:
            continue

        days_since_last = (today - cycle.last_purchased_at).days
        avg_days = round(cycle.avg_interval_days)

        if days_until < 0:
            reason = (
                f"평균 {avg_days}일마다 구매하는 상품이에요. "
                f"마지막 구매 후 {days_since_last}일이 지나 다시 준비할 시기가 되었어요."
            )
            # Mild urgency bonus for products that are overdue, capped.
            score = min(base_score + min(10, abs(days_until) // 3), current_app.config["SCORE_MAX"])
        else:
            reason = (
                f"평균 {avg_days}일마다 구매하는 상품이에요. "
                f"지난 구매 후 {days_since_last}일이 지나 곧 다시 필요할 것으로 예상돼요."
            )
            score = base_score

        candidates.append(
            {
                "product_id": product_id,
                "type": TYPE_REORDER,
                "score": score,
                "reason": reason,
                "expected_date": cycle.expected_next_date,
            }
        )

    return candidates
