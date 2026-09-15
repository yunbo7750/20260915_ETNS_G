from datetime import datetime

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Integer, nullable=False, default=0)  # KRW, integer
    image_url = db.Column(db.String(255), nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=100)
    unit = db.Column(db.String(30), nullable=True)  # e.g. "1개", "5개입"

    tags = db.Column(db.String(255), nullable=True)  # comma separated
    season = db.Column(db.String(20), nullable=True)  # 봄/여름/가을/겨울/전체
    target_age = db.Column(db.String(30), nullable=True)  # e.g. "전연령", "5-10세"

    active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": self.price,
            "image_url": self.image_url,
            "stock": self.stock,
            "unit": self.unit,
            "tags": self.tag_list(),
            "season": self.season,
            "target_age": self.target_age,
        }

    def __repr__(self):
        return f"<Product {self.name}>"
