"""Computes per-user, per-product purchase cycle statistics.

This is pure data analysis shared by the ReorderEngine and by the purchase
history screen ("다음 구매 예상" UI, spec section 41).
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func

from app.extensions import db
from app.models import PurchaseHistory
from flask import current_app


@dataclass
class ProductCycle:
    product_id: int
    purchase_count: int
    last_purchased_at: date
    avg_interval_days: Optional[float]
    avg_quantity: float
    expected_next_date: Optional[date]

    @property
    def has_cycle(self) -> bool:
        return self.avg_interval_days is not None

    def days_until_expected(self, today: date) -> Optional[int]:
        if self.expected_next_date is None:
            return None
        return (self.expected_next_date - today).days


def compute_product_cycles(user_id: int) -> dict[int, ProductCycle]:
    """Returns {product_id: ProductCycle} for every product the user has ever bought."""
    purchases = (
        PurchaseHistory.query.filter_by(user_id=user_id)
        .order_by(PurchaseHistory.product_id, PurchaseHistory.purchased_at.asc())
        .all()
    )

    by_product: dict[int, list[PurchaseHistory]] = {}
    for p in purchases:
        by_product.setdefault(p.product_id, []).append(p)

    min_count = current_app.config.get("REORDER_MIN_PURCHASE_COUNT", 2)

    cycles: dict[int, ProductCycle] = {}
    for product_id, records in by_product.items():
        dates = [r.purchased_at for r in records]
        quantities = [r.quantity for r in records]
        last_purchased_at = dates[-1]
        avg_quantity = sum(quantities) / len(quantities)

        avg_interval_days = None
        expected_next_date = None
        if len(dates) >= min_count:
            intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
            intervals = [d for d in intervals if d > 0]
            if intervals:
                avg_interval_days = sum(intervals) / len(intervals)
                expected_next_date = last_purchased_at + timedelta(days=round(avg_interval_days))

        cycles[product_id] = ProductCycle(
            product_id=product_id,
            purchase_count=len(records),
            last_purchased_at=last_purchased_at,
            avg_interval_days=avg_interval_days,
            avg_quantity=avg_quantity,
            expected_next_date=expected_next_date,
        )

    return cycles


def bestseller_product_ids(limit: int = 5) -> set[int]:
    """Product ids with the highest total purchased quantity across every
    user - a simple, transparent "베스트 상품" signal (site-wide sales
    volume), independent of any one user's personal recommendations."""
    rows = (
        db.session.query(
            PurchaseHistory.product_id, func.sum(PurchaseHistory.quantity).label("total_qty")
        )
        .group_by(PurchaseHistory.product_id)
        .order_by(func.sum(PurchaseHistory.quantity).desc())
        .limit(limit)
        .all()
    )
    return {row.product_id for row in rows}
