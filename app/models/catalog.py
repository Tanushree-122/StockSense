from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    products = db.relationship("Product", back_populates="category")

    def __repr__(self):
        return "<Category {}>".format(self.name)


class Supplier(db.Model):
    __tablename__ = "suppliers"
    __table_args__ = (
        db.CheckConstraint(
            "lead_time_days >= 0 AND lead_time_days <= 60", name="lead_time_range"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(255))
    lead_time_days = db.Column(db.Integer, nullable=False, default=3, server_default="3")

    products = db.relationship("Product", back_populates="supplier")

    def __repr__(self):
        return "<Supplier {}>".format(self.name)
