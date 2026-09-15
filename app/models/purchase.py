from datetime import datetime

from app.extensions import db


class PurchaseHistory(db.Model):
    __tablename__ = "purchase_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False, default=1)
    purchased_at = db.Column(db.Date, nullable=False)
    price = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship("Product")

    def __repr__(self):
        return f"<Purchase user={self.user_id} product={self.product_id} at={self.purchased_at}>"
