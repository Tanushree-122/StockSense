from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Alert, Category, Product, Sale, StockMovement
from app.utils.dates import ist_today
from app.utils.formatting import rupees


@pytest.fixture()
def product(app):
    category = Category(name="Groceries")
    db.session.add(category)
    db.session.flush()
    item = Product(
        sku="RICE-5KG", name="Basmati Rice 5 kg", category_id=category.id,
        cost_price=Decimal("410.00"), selling_price=Decimal("485.00"),
        current_stock=18, min_stock=10,
    )
    db.session.add(item)
    db.session.commit()
    return item


def test_product_status(product):
    assert product.status == "ok"
    product.current_stock = 10
    assert product.status == "low"
    product.current_stock = 0
    assert product.status == "out"


def test_duplicate_sku_rejected(product):
    dup = Product(
        sku="RICE-5KG", name="Other", category_id=product.category_id,
        cost_price=1, selling_price=2,
    )
    db.session.add(dup)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_negative_price_rejected(product):
    bad = Product(
        sku="BAD-1", name="Bad", category_id=product.category_id,
        cost_price=-1, selling_price=2,
    )
    db.session.add(bad)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_negative_stock_rejected(product):
    product.current_stock = -1
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_ledger_sign_rules(product):
    ok = StockMovement(
        product_id=product.id, type="STOCK_IN", quantity_change=5, stock_after=23
    )
    db.session.add(ok)
    db.session.commit()
    wrong_sign = StockMovement(
        product_id=product.id, type="SALE", quantity_change=3, stock_after=21
    )
    db.session.add(wrong_sign)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_adjustment_requires_reason(product):
    movement = StockMovement(
        product_id=product.id, type="ADJUSTMENT", quantity_change=-2, stock_after=16
    )
    db.session.add(movement)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
    movement = StockMovement(
        product_id=product.id, type="ADJUSTMENT", quantity_change=-2, stock_after=16,
        reason="DAMAGED",
    )
    db.session.add(movement)
    db.session.commit()


def test_only_one_open_alert_per_product(product):
    first = Alert(product_id=product.id, alert_type="LOW_STOCK", stock_at_alert=8, min_stock_at_alert=10)
    db.session.add(first)
    db.session.commit()
    second = Alert(product_id=product.id, alert_type="LOW_STOCK", stock_at_alert=7, min_stock_at_alert=10)
    db.session.add(second)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_void_consistency_rule(app):
    bad = Sale(sale_date=ist_today(), status="VOIDED", total_amount=0, total_cost=0)
    db.session.add(bad)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_rupee_format_uses_indian_grouping():
    assert rupees(0) == "₹0.00"
    assert rupees(999) == "₹999.00"
    assert rupees(1000) == "₹1,000.00"
    assert rupees(125000) == "₹1,25,000.00"
    assert rupees("12345678.5") == "₹1,23,45,678.50"
    assert rupees(-2500.5) == "-₹2,500.50"
    assert rupees(125000, decimals=0) == "₹1,25,000"
