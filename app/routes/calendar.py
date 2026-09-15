from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import CalendarEvent
from app.services import recommendation_engine
from app.utils import today_local

calendar_bp = Blueprint("calendar", __name__)

EVENT_TYPES = [
    "생일", "자녀생일", "결혼기념일", "학교행사", "한국방문", "해외출국",
    "이사", "명절", "설날", "추석", "크리스마스", "기타",
]


@calendar_bp.route("/calendar")
@login_required
def calendar_view():
    today = today_local()
    events = (
        CalendarEvent.query.filter_by(user_id=current_user.id)
        .order_by(CalendarEvent.event_date.asc())
        .all()
    )
    return render_template(
        "calendar.html", events=events, today=today, event_types=EVENT_TYPES
    )


@calendar_bp.route("/calendar", methods=["POST"])
@login_required
def calendar_create():
    title = request.form.get("title", "").strip()
    event_type = request.form.get("event_type", "기타")
    event_date = request.form.get("event_date")
    description = request.form.get("description", "").strip() or None

    if not title or not event_date:
        flash("일정 제목과 날짜를 입력해주세요.", "danger")
        return redirect(url_for("calendar.calendar_view"))

    event = CalendarEvent(
        user_id=current_user.id,
        title=title,
        event_type=event_type,
        event_date=date.fromisoformat(event_date),
        description=description,
    )
    db.session.add(event)
    db.session.commit()

    # A newly registered event should be reflected in recommendations right
    # away, rather than waiting for the periodic refresh window.
    recommendation_engine.generate_for_user(current_user)

    flash("일정이 등록되었습니다.", "success")
    return redirect(url_for("calendar.calendar_view"))


@calendar_bp.route("/calendar/<int:event_id>/delete", methods=["POST"])
@login_required
def calendar_delete(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    db.session.delete(event)
    db.session.commit()
    recommendation_engine.generate_for_user(current_user)
    flash("일정이 삭제되었습니다.", "info")
    return redirect(url_for("calendar.calendar_view"))


@calendar_bp.route("/api/calendar", methods=["GET"])
@login_required
def api_calendar_list():
    events = CalendarEvent.query.filter_by(user_id=current_user.id).order_by(
        CalendarEvent.event_date.asc()
    ).all()
    return jsonify([e.to_dict() for e in events])


@calendar_bp.route("/api/calendar", methods=["POST"])
@login_required
def api_calendar_create():
    data = request.get_json(force=True)
    event = CalendarEvent(
        user_id=current_user.id,
        title=data.get("title", "").strip(),
        event_type=data.get("event_type", "기타"),
        event_date=date.fromisoformat(data["event_date"]),
        description=data.get("description"),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@calendar_bp.route("/api/calendar/<int:event_id>", methods=["PUT"])
@login_required
def api_calendar_update(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    data = request.get_json(force=True)

    if "title" in data:
        event.title = data["title"]
    if "event_type" in data:
        event.event_type = data["event_type"]
    if "event_date" in data:
        event.event_date = date.fromisoformat(data["event_date"])
    if "description" in data:
        event.description = data["description"]

    db.session.commit()
    return jsonify(event.to_dict())


@calendar_bp.route("/api/calendar/<int:event_id>", methods=["DELETE"])
@login_required
def api_calendar_delete(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    db.session.delete(event)
    db.session.commit()
    return jsonify({"deleted": True})
