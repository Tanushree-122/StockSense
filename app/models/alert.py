from app.constants import ALERT_STATUSES, ALERT_TYPES, EMAIL_STATUSES, sql_in
from app.extensions import db
from app.utils.dates import now_utc


class Alert(db.Model):
    __tablename__ = "alerts"
    __table_args__ = (
        db.CheckConstraint(sql_in("alert_type", ALERT_TYPES), name="alert_type_valid"),
        db.CheckConstraint(sql_in("status", ALERT_STATUSES), name="status_valid"),
        db.CheckConstraint(sql_in("email_status", EMAIL_STATUSES), name="email_status_valid"),
        db.CheckConstraint("stock_at_alert >= 0", name="stock_at_alert_non_negative"),
        db.CheckConstraint("min_stock_at_alert >= 0", name="min_stock_at_alert_non_negative"),
        db.CheckConstraint(
            "(status = 'RESOLVED') = (resolved_at IS NOT NULL)", name="resolved_consistency"
        ),
        db.Index("ix_alerts_product_status", "product_id", "status"),
        # The database itself guarantees at most one OPEN alert per product.
        db.Index(
            "uq_alerts_one_open_per_product",
            "product_id",
            unique=True,
            postgresql_where=db.text("status = 'OPEN'"),
            sqlite_where=db.text("status = 'OPEN'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    alert_type = db.Column(db.String(15), nullable=False)
    stock_at_alert = db.Column(db.Integer, nullable=False)
    min_stock_at_alert = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False, default="OPEN", server_default="OPEN")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    resolved_at = db.Column(db.DateTime(timezone=True))
    email_status = db.Column(
        db.String(12), nullable=False, default="NOT_SENT", server_default="NOT_SENT"
    )
    email_sent_at = db.Column(db.DateTime(timezone=True))
    email_error = db.Column(db.String(255))

    product = db.relationship("Product")
