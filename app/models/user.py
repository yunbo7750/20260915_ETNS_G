from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'

    name = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    assignment_start_date = db.Column(db.Date, nullable=True)
    assignment_end_date = db.Column(db.Date, nullable=True)

    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    family_members = db.relationship(
        "FamilyMember", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    preferences = db.relationship(
        "Preference", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    purchases = db.relationship(
        "PurchaseHistory", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    calendar_events = db.relationship(
        "CalendarEvent", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    recommendations = db.relationship(
        "Recommendation", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    notifications = db.relationship(
        "Notification", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    cart = db.relationship(
        "Cart", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def children_count(self) -> int:
        return self.family_members.filter_by(relation="자녀").count()

    @property
    def has_spouse(self) -> bool:
        return self.family_members.filter_by(relation="배우자").count() > 0

    @property
    def family_size(self) -> int:
        return self.family_members.count() + 1

    def __repr__(self):
        return f"<User {self.username}>"
