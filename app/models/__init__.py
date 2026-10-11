"""Importing every model here lets migrations and create_all() see all tables."""
from app.models.alert import Alert
from app.models.catalog import Category, Supplier
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.stock_movement import StockMovement
from app.models.user import User

__all__ = [
    "Alert",
    "Category",
    "Supplier",
    "Product",
    "Sale",
    "SaleItem",
    "StockMovement",
    "User",
]
