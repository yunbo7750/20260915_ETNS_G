"""ENGINE 2 - LIFE CALENDAR ENGINE

Recommends products relevant to the user's upcoming registered life events
(birthdays, trips home, holidays, moving, etc.).
"""
from flask import current_app

from app.models import Product, CalendarEvent
from app.models.recommendation import TYPE_LIFE_EVENT
from app.utils import today_local

MAX_PRODUCTS_PER_EVENT = 3


def _matching_products(event_type: str):
    tag_map = current_app.config.get("EVENT_TYPE_PRODUCT_TAGS", {})
    tags = tag_map.get(event_type) or tag_map.get("기타", [])

    products = Product.query.filter_by(active=True).all()
    matches = []
    for product in products:
        product_tags = set(product.tag_list() + [product.category])
        if product_tags.intersection(tags):
            matches.append(product)
    return matches[:MAX_PRODUCTS_PER_EVENT]


def generate(user) -> list[dict]:
    today = today_local()
    checkpoints = current_app.config.get("EVENT_RECOMMENDATION_DAYS", [30, 14, 7, 3])
    max_lookahead = max(checkpoints) if checkpoints else 30
    base_score = current_app.config.get("SCORE_LIFE_EVENT", 30)

    events = CalendarEvent.query.filter(
        CalendarEvent.user_id == user.id, CalendarEvent.event_date >= today
    ).all()

    candidates = []
    for event in events:
        days_until = (event.event_date - today).days
        if days_until > max_lookahead:
            continue

        proximity_bonus = round((max_lookahead - days_until) / max_lookahead * 10)
        score = min(base_score + proximity_bonus, current_app.config["SCORE_MAX"])

        if days_until == 0:
            reason = f"'{event.title}' 일정이 오늘이에요. 지금 준비해보세요."
        else:
            reason = f"'{event.title}' 일정까지 {days_until}일 남아 미리 준비하면 좋은 상품이에요."

        for product in _matching_products(event.event_type):
            candidates.append(
                {
                    "product_id": product.id,
                    "type": TYPE_LIFE_EVENT,
                    "score": score,
                    "reason": reason,
                    "expected_date": event.event_date,
                }
            )

    return candidates
