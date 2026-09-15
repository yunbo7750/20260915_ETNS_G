from datetime import datetime

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    type = db.Column(db.String(30), nullable=False)  # RECOMMENDATION | LIFE_EVENT | SYSTEM
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(255), nullable=False)

    reference_type = db.Column(db.String(30), nullable=True)  # e.g. "recommendation"
    reference_id = db.Column(db.Integer, nullable=True)

    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Notification {self.title} for user={self.user_id}>"
