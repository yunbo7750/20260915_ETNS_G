from app.extensions import db


class Preference(db.Model):
    """A user's like/dislike, either for a whole category or a specific product."""

    __tablename__ = "preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    target_type = db.Column(db.String(20), nullable=False)  # 'category' | 'product'
    category = db.Column(db.String(80), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)

    sentiment = db.Column(db.String(10), nullable=False, default="like")  # 'like' | 'dislike'

    product = db.relationship("Product")

    def __repr__(self):
        target = self.category or self.product_id
        return f"<Preference user={self.user_id} {self.sentiment} {self.target_type}:{target}>"
