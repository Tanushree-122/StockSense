from app.constants import SALE_STATUSES, sql_in
from app.extensions import db
from app.utils.dates import now_utc


class Sale(db.Model):
    __tablename__ = "sales"
    __table_args__ = (
        db.CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
        db.CheckConstraint("total_cost >= 0", name="total_cost_non_negative"),
        db.CheckConstraint(sql_in("status", SALE_STATUSES), name="status_valid"),
        db.CheckConstraint(
            "(status = 'COMPLETED' AND voided_at IS NULL) OR "
            "(status = 'VOIDED' AND voided_at IS NOT NULL AND void_reason IS NOT NULL)",
            name="void_consistency",
        ),
        db.Index("ix_sales_sale_date", "sale_date"),
        db.Index("ix_sales_status", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # Set right after the first insert, because the number is built from the id.
    bill_no = db.Column(db.String(20), unique=True)
    sold_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    sale_date = db.Column(db.Date, nullable=False)  # the IST calendar date
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(12), nullable=False, default="COMPLETED", server_default="COMPLETED")
    voided_at = db.Column(db.DateTime(timezone=True))
    void_reason = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    items = db.relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def profit(self):
        return self.total_amount - self.total_cost

    def __repr__(self):
        return "<Sale {}>".format(self.bill_no or self.id)


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="quantity_positive"),
        db.CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        db.CheckConstraint("unit_cost >= 0", name="unit_cost_non_negative"),
        db.CheckConstraint("line_total >= 0", name="line_total_non_negative"),
        db.CheckConstraint("line_cost >= 0", name="line_cost_non_negative"),
        db.UniqueConstraint("sale_id", "product_id", name="one_line_per_product"),
    )

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)  # snapshot
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False)  # snapshot
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    line_cost = db.Column(db.Numeric(12, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")
