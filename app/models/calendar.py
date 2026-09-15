from datetime import datetime

from app.extensions import db


class CalendarEvent(db.Model):
    __tablename__ = "calendar_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(120), nullable=False)
    event_type = db.Column(db.String(40), nullable=False)  # 생일/한국방문/이사/명절/기타...
    event_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    # Free-text hints ("이도윤 축구 좋아함", "매운맛 선호", "비타민 필요" ...)
    # that the LifeCalendarEngine matches against product tags/name/category
    # to recommend products beyond the fixed event-type mapping.
    keywords = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def keyword_list(self):
        if not self.keywords:
            return []
        import re

        return [t for t in re.split(r"[,\s]+", self.keywords.strip()) if len(t) >= 2]

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat(),
            "description": self.description,
            "keywords": self.keywords,
        }

    def __repr__(self):
        return f"<CalendarEvent {self.title} ({self.event_date})>"
