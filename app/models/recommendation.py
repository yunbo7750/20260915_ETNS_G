from datetime import datetime

from app.extensions import db

# Recommendation types produced by the three engines.
TYPE_REORDER = "REORDER"
TYPE_LIFE_EVENT = "LIFE_EVENT"
TYPE_PERSONAL = "PERSONAL"


class Recommendation(db.Model):
    """A single recommended product for a user.

    This doubles as the recommendation log (spec sections 32/33): every row
    already carries score/reason/created_at plus clicked_at/added_to_cart_at,
    so admin analytics (click-through rate, cart conversion) are computed
    directly off this table instead of a separate log table.
    """

    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    type = db.Column(db.String(20), nullable=False)  # REORDER | LIFE_EVENT | PERSONAL
    combined_types = db.Column(db.String(60), nullable=True)  # e.g. "REORDER+PERSONAL"

    score = db.Column(db.Integer, nullable=False, default=0)
    reason = db.Column(db.Text, nullable=False)
    expected_date = db.Column(db.Date, nullable=True)

    is_clicked = db.Column(db.Boolean, default=False, nullable=False)
    is_added_to_cart = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clicked_at = db.Column(db.DateTime, nullable=True)
    added_to_cart_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship("Product")

    def mark_clicked(self):
        if not self.is_clicked:
            self.is_clicked = True
            self.clicked_at = datetime.utcnow()

    def mark_added_to_cart(self):
        if not self.is_added_to_cart:
            self.is_added_to_cart = True
            self.added_to_cart_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "product": self.product.to_dict() if self.product else None,
            "type": self.type,
            "combined_types": self.combined_types,
            "score": self.score,
            "reason": self.reason,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "is_clicked": self.is_clicked,
            "is_added_to_cart": self.is_added_to_cart,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Recommendation user={self.user_id} product={self.product_id} type={self.type} score={self.score}>"
