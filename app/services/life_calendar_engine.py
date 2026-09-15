"""ENGINE 2 - LIFE CALENDAR ENGINE

Recommends products relevant to the user's upcoming registered life events
(birthdays, trips home, holidays, moving, etc.), plus anything matching the
free-text keywords the user optionally attaches to an event (a child's
interests, a health note, a taste preference, ...).
"""
from flask import current_app

from app.models import Product, CalendarEvent
from app.models.recommendation import TYPE_LIFE_EVENT
from app.utils import today_local


def _type_matched_products(event_type: str, limit: int):
    tag_map = current_app.config.get("EVENT_TYPE_PRODUCT_TAGS", {})
    tags = tag_map.get(event_type) or tag_map.get("기타", [])

    matches = []
    for product in Product.query.filter_by(active=True).all():
        product_tags = set(product.tag_list() + [product.category])
        if product_tags.intersection(tags):
            matches.append(product)
    return matches[:limit]


def _keyword_matched_products(keywords: list[str], limit: int):
    """Matches products whose name/category/description/tags mention one of
    the given free-text keywords (or vice versa) - e.g. keyword '비타민'
    matches a product named '어린이 비타민 젤리', keyword '매운맛' matches a
    product tagged '매운맛'."""
    if not keywords:
        return []

    matches = []
    for product in Product.query.filter_by(active=True).all():
        haystack = " ".join(
            [product.name, product.category, product.description or ""] + product.tag_list()
        ).lower()

        hit = None
        for kw in keywords:
            kw_l = kw.lower()
            if kw_l in haystack or any(
                kw_l in tag.lower() or tag.lower() in kw_l for tag in product.tag_list()
            ):
                hit = kw
                break

        if hit:
            matches.append((product, hit))
        if len(matches) >= limit:
            break

    return matches


def generate(user) -> list[dict]:
    today = today_local()
    checkpoints = current_app.config.get("EVENT_RECOMMENDATION_DAYS", [30, 14, 7, 3])
    max_lookahead = max(checkpoints) if checkpoints else 30
    base_score = current_app.config.get("SCORE_LIFE_EVENT", 30)
    keyword_bonus = current_app.config.get("SCORE_LIFE_EVENT_KEYWORD_BONUS", 15)
    type_limit = current_app.config.get("EVENT_TYPE_MAX_PRODUCTS", 3)
    keyword_limit = current_app.config.get("EVENT_KEYWORD_MAX_PRODUCTS", 3)
    score_max = current_app.config.get("SCORE_MAX", 100)

    events = CalendarEvent.query.filter(
        CalendarEvent.user_id == user.id, CalendarEvent.event_date >= today
    ).all()

    candidates = []
    for event in events:
        days_until = (event.event_date - today).days
        if days_until > max_lookahead:
            continue

        proximity_bonus = round((max_lookahead - days_until) / max_lookahead * 10)
        type_score = base_score + proximity_bonus

        if days_until == 0:
            date_reason = f"'{event.title}' 일정이 오늘이에요. 지금 준비해보세요."
        else:
            date_reason = f"'{event.title}' 일정까지 {days_until}일 남아 미리 준비하면 좋은 상품이에요."

        # product_id -> {"score": int, "reasons": [str, ...]}
        merged: dict[int, dict] = {}

        for product in _type_matched_products(event.event_type, type_limit):
            merged[product.id] = {"score": type_score, "reasons": [date_reason]}

        for product, keyword in _keyword_matched_products(event.keyword_list(), keyword_limit):
            entry = merged.setdefault(product.id, {"score": 0, "reasons": []})
            entry["score"] = min(entry["score"] + base_score + keyword_bonus, score_max)
            entry["reasons"].append(
                f"'{event.title}' 일정에 등록하신 '{keyword}' 키워드와 어울리는 상품이에요."
            )

        for product_id, entry in merged.items():
            candidates.append(
                {
                    "product_id": product_id,
                    "type": TYPE_LIFE_EVENT,
                    "score": entry["score"],
                    "reason": " ".join(entry["reasons"]),
                    "expected_date": event.event_date,
                }
            )

    return candidates
