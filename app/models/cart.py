from datetime import datetime

from app.extensions import db


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("CartItem", backref="cart", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items)

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<Cart user={self.user_id}>"


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product")

    @property
    def subtotal(self):
        return self.product.price * self.quantity if self.product else 0

    def to_dict(self):
        return {
            "id": self.id,
            "product": self.product.to_dict() if self.product else None,
            "quantity": self.quantity,
            "subtotal": self.subtotal,
        }

    def __repr__(self):
        return f"<CartItem product={self.product_id} qty={self.quantity}>"
