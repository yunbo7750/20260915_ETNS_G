"""RECOMMENDATION ENGINE - orchestrates the three underlying engines.

    ReorderEngine + LifeCalendarEngine + PersonalLifeEngine
        -> merge duplicates -> score -> reason -> persist -> notify

This module is the only thing the rest of the app talks to. Swapping the
rule-based engines below for an AI/ML-based engine later only requires
changing what `_CANDIDATE_ENGINES` calls - callers (routes, templates) never
need to change.
"""
from datetime import datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import Product, Recommendation
from app.models.recommendation import TYPE_REORDER, TYPE_LIFE_EVENT, TYPE_PERSONAL
from app.services import reorder_engine, life_calendar_engine, personal_life_engine
from app.services.notification_service import notify_new_recommendations

# Each engine exposes generate(user) -> list[{product_id, type, score, reason, expected_date}]
_CANDIDATE_ENGINES = [reorder_engine, life_calendar_engine, personal_life_engine]

GROUP_LABELS = {
    TYPE_REORDER: "다시 구매할 시기",
    TYPE_LIFE_EVENT: "일정에 맞춰 준비",
    TYPE_PERSONAL: "나에게 맞는 추천",
}


def _merge_candidates(candidate_lists: list[list[dict]]) -> dict[int, dict]:
    """Merges candidates for the same product across engines into one entry,
    combining their scores and reasons (spec section 35)."""
    merged: dict[int, dict] = {}
    score_max = current_app.config.get("SCORE_MAX", 100)

    for candidates in candidate_lists:
        for c in candidates:
            pid = c["product_id"]
            if pid not in merged:
                merged[pid] = {
                    "product_id": pid,
                    "types": [c["type"]],
                    "score": c["score"],
                    "reasons": [c["reason"]],
                    "expected_date": c["expected_date"],
                }
            else:
                entry = merged[pid]
                if c["type"] not in entry["types"]:
                    entry["types"].append(c["type"])
                entry["score"] = min(entry["score"] + c["score"], score_max)
                entry["reasons"].append(c["reason"])
                if c["expected_date"] and (
                    entry["expected_date"] is None or c["expected_date"] < entry["expected_date"]
                ):
                    entry["expected_date"] = c["expected_date"]

    return merged


def _dedupe_reasons(reasons: list[str]) -> str:
    seen = []
    for r in reasons:
        if r not in seen:
            seen.append(r)
    return " ".join(seen)


def generate_for_user(user, persist: bool = True):
    """Runs all three engines for `user`, merges/dedupes/scores the results,
    and (by default) persists them as a fresh Recommendation batch."""
    candidate_lists = [engine.generate(user) for engine in _CANDIDATE_ENGINES]
    merged = _merge_candidates(candidate_lists)

    results = []
    for pid, entry in merged.items():
        combined_types = "+".join(entry["types"]) if len(entry["types"]) > 1 else None
        results.append(
            {
                "product_id": pid,
                "type": entry["types"][0],
                "combined_types": combined_types,
                "score": entry["score"],
                "reason": _dedupe_reasons(entry["reasons"]),
                "expected_date": entry["expected_date"],
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)

    if not persist:
        return results

    batch_time = datetime.utcnow()
    rows = []
    for r in results:
        row = Recommendation(
            user_id=user.id,
            product_id=r["product_id"],
            type=r["type"],
            combined_types=r["combined_types"],
            score=r["score"],
            reason=r["reason"],
            expected_date=r["expected_date"],
            created_at=batch_time,
        )
        db.session.add(row)
        rows.append(row)
    db.session.commit()

    if rows:
        notify_new_recommendations(user, rows)

    return rows


def get_current_batch(user, force_refresh: bool = False):
    """Returns the user's current recommendation batch, regenerating it if
    the last batch is older than RECOMMENDATION_REFRESH_HOURS (so the home
    page doesn't recompute recommendations on every single request)."""
    refresh_hours = current_app.config.get("RECOMMENDATION_REFRESH_HOURS", 12)

    latest = (
        Recommendation.query.filter_by(user_id=user.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    stale = latest is not None and (
        datetime.utcnow() - latest.created_at > timedelta(hours=refresh_hours)
    )

    if force_refresh or latest is None or stale:
        return generate_for_user(user)

    return (
        Recommendation.query.filter_by(user_id=user.id, created_at=latest.created_at)
        .order_by(Recommendation.score.desc())
        .all()
    )


def group_by_type(recommendations: list[Recommendation]) -> dict:
    """Groups a recommendation batch into the three home-screen sections."""
    groups = {TYPE_REORDER: [], TYPE_LIFE_EVENT: [], TYPE_PERSONAL: []}
    for rec in recommendations:
        groups.setdefault(rec.type, []).append(rec)
    return groups


def get_fallback_products(limit: int = 6):
    """Used only when a user genuinely has no personalized recommendations
    yet (spec section 37). Explicitly NOT labeled as personalized."""
    return (
        Product.query.filter_by(active=True)
        .order_by(Product.created_at.desc())
        .limit(limit)
        .all()
    )
