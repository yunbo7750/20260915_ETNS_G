"""ENGINE 3 - PERSONAL LIFE ENGINE

Recommends products based on the user's personal profile: family
composition (children present/ages), explicit preferences, and category
purchase frequency. Two users with different profiles get different results.
"""
from collections import Counter

from flask import current_app

from app.models import Product
from app.models.recommendation import TYPE_PERSONAL

FREQUENT_CATEGORY_THRESHOLD = 3


def generate(user) -> list[dict]:
    base = current_app.config.get("SCORE_PERSONAL", 20)
    child_bonus = round(base * 0.5)
    category_like_bonus = round(base * 0.5)
    product_like_bonus = round(base * 0.75)
    frequent_category_bonus = round(base * 0.5)

    preferences = list(user.preferences)
    disliked_categories = {
        p.category for p in preferences if p.sentiment == "dislike" and p.target_type == "category"
    }
    disliked_product_ids = {
        p.product_id for p in preferences if p.sentiment == "dislike" and p.target_type == "product"
    }
    liked_categories = {
        p.category for p in preferences if p.sentiment == "like" and p.target_type == "category"
    }
    liked_product_ids = {
        p.product_id for p in preferences if p.sentiment == "like" and p.target_type == "product"
    }

    has_children = user.children_count > 0
    child_categories = set(current_app.config.get("CHILD_PRODUCT_CATEGORIES", []))

    purchase_counts = Counter()
    for purchase in user.purchases:
        if purchase.product:
            purchase_counts[purchase.product.category] += 1
    frequent_categories = {
        category for category, count in purchase_counts.items() if count >= FREQUENT_CATEGORY_THRESHOLD
    }

    candidates = []
    products = Product.query.filter_by(active=True).all()
    for product in products:
        if product.category in disliked_categories or product.id in disliked_product_ids:
            continue

        score = 0
        reasons = []

        if has_children and product.category in child_categories:
            score += child_bonus
            reasons.append("자녀가 있어 어린이 관련 상품을 추천해요.")

        if product.category in liked_categories:
            score += category_like_bonus
            reasons.append(f"선호하시는 '{product.category}' 카테고리 상품이에요.")

        if product.id in liked_product_ids:
            score += product_like_bonus
            reasons.append("평소 선호 상품으로 등록하신 항목이에요.")

        if product.category in frequent_categories:
            score += frequent_category_bonus
            reasons.append(f"'{product.category}' 카테고리를 자주 구매하셨어요.")

        if score <= 0:
            continue

        candidates.append(
            {
                "product_id": product.id,
                "type": TYPE_PERSONAL,
                "score": min(score, current_app.config["SCORE_MAX"]),
                "reason": " ".join(reasons),
                "expected_date": None,
            }
        )

    return candidates
