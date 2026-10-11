from app.constants import ADJUSTMENT_REASONS, MOVEMENT_TYPES, sql_in
from app.extensions import db
from app.utils.dates import now_utc


class StockMovement(db.Model):
    """The stock ledger: every change to a product's stock is one row here."""

    __tablename__ = "stock_movements"
    __table_args__ = (
        db.CheckConstraint(sql_in("type", MOVEMENT_TYPES), name="type_valid"),
        db.CheckConstraint("quantity_change <> 0", name="quantity_change_not_zero"),
        db.CheckConstraint("stock_after >= 0", name="stock_after_non_negative"),
        db.CheckConstraint(
            "(type IN ('OPENING','STOCK_IN','SALE_VOID') AND quantity_change > 0) OR "
            "(type = 'SALE' AND quantity_change < 0) OR "
            "(type = 'ADJUSTMENT')",
            name="sign_matches_type",
        ),
        db.CheckConstraint(
            "type <> 'ADJUSTMENT' OR reason IS NOT NULL", name="adjustment_needs_reason"
        ),
        db.CheckConstraint(
            "reason IS NULL OR " + sql_in("reason", ADJUSTMENT_REASONS), name="reason_valid"
        ),
        db.Index("ix_stock_movements_product_created", "product_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    type = db.Column(db.String(12), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)
    stock_after = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(30))
    note = db.Column(db.String(255))
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id", ondelete="RESTRICT"))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    product = db.relationship("Product")
    sale = db.relationship("Sale")
