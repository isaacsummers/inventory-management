"""
Tests for orders API endpoints.
"""
import pytest


class TestOrdersEndpoints:
    """Test suite for order-related endpoints."""

    def test_get_all_orders(self, client):
        """Test getting all orders."""
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first_order = data[0]
        for field in ("id", "order_number", "customer", "items", "status",
                      "warehouse", "category", "order_date", "total_value"):
            assert field in first_order

    def test_order_ids_are_unique(self, client):
        """Order ids must be unique; duplicates double-count revenue."""
        data = client.get("/api/orders").json()

        ids = [order["id"] for order in data]
        assert len(ids) == len(set(ids))

    def test_order_numbers_are_unique(self, client):
        """Order numbers must be unique."""
        data = client.get("/api/orders").json()

        numbers = [order["order_number"] for order in data]
        assert len(numbers) == len(set(numbers))

    def test_order_total_value_calculation(self, client):
        """Test that each order's total matches the sum of its line items."""
        data = client.get("/api/orders").json()

        for order in data:
            calculated_total = sum(
                item["quantity"] * item["unit_price"] for item in order["items"]
            )
            assert abs(order["total_value"] - calculated_total) < 0.01

    def test_dashboard_revenue_matches_orders(self, client):
        """Dashboard revenue should equal the sum of all order values."""
        orders = client.get("/api/orders").json()
        summary = client.get("/api/dashboard/summary").json()

        expected = sum(order["total_value"] for order in orders)
        assert abs(summary["total_orders_value"] - expected) < 0.01

    def test_get_orders_by_warehouse(self, client):
        """Test filtering orders by warehouse."""
        response = client.get("/api/orders?warehouse=Tokyo")
        assert response.status_code == 200

        for order in response.json():
            assert order["warehouse"] == "Tokyo"
