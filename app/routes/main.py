from datetime import date
from types import SimpleNamespace

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import FamilyMember, Preference, CalendarEvent, Notification, Product, Recommendation
from app.models.recommendation import TYPE_REORDER
from app.services import recommendation_engine
from app.utils import today_local

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def home():
    recommendations = recommendation_engine.get_current_batch(current_user)
    home_limit = current_app.config.get("HOME_MAX_RECOMMENDATIONS", 6)

    top_recommendations = list(recommendations)[:home_limit]
    groups = recommendation_engine.group_by_type(top_recommendations)

    fallback_products = None
    if not recommendations:
        fallback_products = recommendation_engine.get_fallback_products(home_limit)

    today = today_local()
    upcoming_events = (
        CalendarEvent.query.filter(
            CalendarEvent.user_id == current_user.id, CalendarEvent.event_date >= today
        )
        .order_by(CalendarEvent.event_date.asc())
        .limit(3)
        .all()
    )

    return render_template(
        "home.html",
        groups=groups,
        fallback_products=fallback_products,
        upcoming_events=upcoming_events,
        today=today,
    )


@main_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if request.method == "POST":
        current_user.country = request.form.get("country", "").strip() or current_user.country
        current_user.city = request.form.get("city", "").strip() or current_user.city

        if request.form.get("has_spouse") and not current_user.has_spouse:
            db.session.add(FamilyMember(user_id=current_user.id, relation="배우자"))

        children_count = int(request.form.get("children_count") or 0)
        existing_children = current_user.children_count
        for _ in range(max(0, children_count - existing_children)):
            db.session.add(FamilyMember(user_id=current_user.id, relation="자녀"))

        for category in request.form.getlist("preferred_categories"):
            exists = Preference.query.filter_by(
                user_id=current_user.id, target_type="category", category=category, sentiment="like"
            ).first()
            if not exists:
                db.session.add(
                    Preference(
                        user_id=current_user.id,
                        target_type="category",
                        category=category,
                        sentiment="like",
                    )
                )

        for product_id in request.form.getlist("favorite_products"):
            exists = Preference.query.filter_by(
                user_id=current_user.id, target_type="product", product_id=int(product_id), sentiment="like"
            ).first()
            if not exists:
                db.session.add(
                    Preference(
                        user_id=current_user.id,
                        target_type="product",
                        product_id=int(product_id),
                        sentiment="like",
                    )
                )

        current_user.onboarding_completed = True
        db.session.commit()
        recommendation_engine.generate_for_user(current_user)
        flash("온보딩이 완료되었어요. 맞춤 추천을 준비할게요!", "success")
        return redirect(url_for("main.home"))

    categories = [row[0] for row in db.session.query(Product.category).distinct().all()]
    popular_products = Product.query.filter_by(active=True).limit(12).all()
    return render_template("onboarding.html", categories=categories, popular_products=popular_products)


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.country = request.form.get("country", "").strip()
        current_user.city = request.form.get("city", "").strip()

        start_date = request.form.get("assignment_start_date")
        end_date = request.form.get("assignment_end_date")
        current_user.assignment_start_date = date.fromisoformat(start_date) if start_date else None
        current_user.assignment_end_date = date.fromisoformat(end_date) if end_date else None

        db.session.commit()
        flash("프로필이 저장되었습니다.", "success")
        return redirect(url_for("main.profile"))

    categories = [row[0] for row in db.session.query(Product.category).distinct().all()]
    return render_template("profile.html", categories=categories)


@main_bp.route("/profile/family", methods=["POST"])
@login_required
def add_family_member():
    relation = request.form.get("relation", "기타")
    name = request.form.get("name", "").strip() or None
    birth_date = request.form.get("birth_date")
    interests = request.form.get("interests", "").strip() or None

    member = FamilyMember(
        user_id=current_user.id,
        relation=relation,
        name=name,
        birth_date=date.fromisoformat(birth_date) if birth_date else None,
        interests=interests,
    )
    db.session.add(member)
    db.session.commit()
    recommendation_engine.generate_for_user(current_user)
    flash("가족 정보가 추가되었습니다.", "success")
    return redirect(url_for("main.profile"))


@main_bp.route("/profile/family/<int:member_id>/delete", methods=["POST"])
@login_required
def delete_family_member(member_id):
    member = FamilyMember.query.filter_by(id=member_id, user_id=current_user.id).first_or_404()
    db.session.delete(member)
    db.session.commit()
    recommendation_engine.generate_for_user(current_user)
    return redirect(url_for("main.profile"))


@main_bp.route("/profile/preferences", methods=["POST"])
@login_required
def add_preference():
    target_type = request.form.get("target_type")
    sentiment = request.form.get("sentiment", "like")
    category = request.form.get("category") or None
    product_id = request.form.get("product_id") or None

    pref = Preference(
        user_id=current_user.id,
        target_type=target_type,
        category=category if target_type == "category" else None,
        product_id=int(product_id) if target_type == "product" and product_id else None,
        sentiment=sentiment,
    )
    db.session.add(pref)
    db.session.commit()
    recommendation_engine.generate_for_user(current_user)
    flash("선호도가 저장되었습니다.", "success")
    return redirect(url_for("main.profile"))


@main_bp.route("/profile/preferences/<int:pref_id>/delete", methods=["POST"])
@login_required
def delete_preference(pref_id):
    pref = Preference.query.filter_by(id=pref_id, user_id=current_user.id).first_or_404()
    db.session.delete(pref)
    db.session.commit()
    recommendation_engine.generate_for_user(current_user)
    return redirect(url_for("main.profile"))


@main_bp.route("/notifications")
@login_required
def notifications():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    return render_template("notifications.html", notifications=items)


@main_bp.route("/api/notifications")
@login_required
def api_notifications():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )
    return jsonify([n.to_dict() for n in items])


@main_bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def api_notification_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify(notification.to_dict())


def _pick_demo_notification(user):
    """Picks the notification/recommendation pair to feature in the mobile
    push demo. Prefers a REORDER ("다시 구매할 시기") notification since
    that's the clearest "구매 시기가 다가왔다" story, falling back to
    whatever recommendation-linked notification is most recent."""
    notifications = (
        Notification.query.filter_by(user_id=user.id, reference_type="recommendation")
        .order_by(Notification.created_at.desc())
        .all()
    )

    fallback_pick = None
    for n in notifications:
        rec = Recommendation.query.get(n.reference_id)
        if not rec:
            continue
        if rec.type == TYPE_REORDER:
            return n, rec
        if fallback_pick is None:
            fallback_pick = (n, rec)

    # Only one notification is saved per recommendation batch (see
    # notify_new_recommendations), so a REORDER-specific one may not exist
    # even though a REORDER recommendation does. Synthesize the same style
    # of notification directly from the current batch so the "구매 시기
    # 도래" story can still be demoed.
    reorder_recs = [
        r for r in recommendation_engine.get_current_batch(user) if r.type == TYPE_REORDER
    ]
    if reorder_recs:
        rec = max(reorder_recs, key=lambda r: r.score)
        others = len(reorder_recs) - 1
        message = rec.product.name + (f" 외 {others}개" if others > 0 else "") + " 상품을 다시 준비할 시기예요."
        synthetic = SimpleNamespace(
            title="다시 구매할 시기가 된 상품이 있어요",
            message=message,
            created_at=rec.created_at,
        )
        return synthetic, rec

    return fallback_pick or (None, None)


_WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


@main_bp.route("/notifications/demo")
@login_required
def notification_mobile_demo():
    notification, recommendation = _pick_demo_notification(current_user)
    today = today_local()
    today_str = f"{today.month}월 {today.day}일 {_WEEKDAYS_KR[today.weekday()]}요일"
    return render_template(
        "mobile_notification_demo.html",
        notification=notification,
        recommendation=recommendation,
        today_str=today_str,
    )
