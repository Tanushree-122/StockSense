from app.extensions import db
from app.utils.dates import now_utc


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("cost_price >= 0", name="cost_price_non_negative"),
        db.CheckConstraint("selling_price >= 0", name="selling_price_non_negative"),
        db.CheckConstraint("current_stock >= 0", name="current_stock_non_negative"),
        db.CheckConstraint("min_stock >= 0", name="min_stock_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    supplier_id = db.Column(
        db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True
    )
    cost_price = db.Column(db.Numeric(12, 2), nullable=False)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False)
    # Only stock_service may change current_stock (rule R2).
    current_stock = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    min_stock = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc
    )

    category = db.relationship("Category", back_populates="products")
    supplier = db.relationship("Supplier", back_populates="products")

    @property
    def status(self):
        """'out', 'low', or 'ok' based on current and minimum stock."""
        if self.current_stock <= 0:
            return "out"
        if self.current_stock <= self.min_stock:
            return "low"
        return "ok"

    def __repr__(self):
        return "<Product {}>".format(self.sku)
