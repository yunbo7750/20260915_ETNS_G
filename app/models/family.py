from datetime import date

from app.extensions import db


class FamilyMember(db.Model):
    __tablename__ = "family_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    relation = db.Column(db.String(30), nullable=False)  # 배우자 / 자녀 / 기타
    name = db.Column(db.String(80), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    interests = db.Column(db.String(255), nullable=True)  # comma separated tags

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    def interest_list(self):
        if not self.interests:
            return []
        return [i.strip() for i in self.interests.split(",") if i.strip()]

    def __repr__(self):
        return f"<FamilyMember {self.relation} of user {self.user_id}>"
