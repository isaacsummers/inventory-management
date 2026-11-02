"""
Tests for restocking API endpoints and the demand fields that support them.
"""
from datetime import datetime, timedelta

import pytest


class TestDemandRestockFields:
    """Demand forecasts carry the data needed to price and schedule a restock."""

    def test_demand_forecast_restock_fields_structure(self, client):
        """Test that every forecast has cost, stock and lead time fields."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert "unit_cost" in forecast
            assert "quantity_on_hand" in forecast
            assert "lead_time_days" in forecast

    def test_demand_forecast_restock_field_types(self, client):
        """Test that restock fields have valid types and ranges."""
        response = client.get("/api/demand")
        data = response.json()

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["quantity_on_hand"], int)
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["quantity_on_hand"] >= 0
            assert forecast["lead_time_days"] > 0

    def test_decreasing_demand_item_has_no_shortfall(self, client):
        """Test that the decreasing-trend item is already stocked for its forecast."""
        data = client.get("/api/demand").json()

        for forecast in data:
            if forecast["trend"] == "decreasing":
                assert forecast["quantity_on_hand"] >= forecast["forecasted_demand"]


class TestRestockOrderEndpoints:
    """Test suite for restocking order endpoints."""

    def test_get_restock_orders_empty(self, client, clean_restock_orders):
        """Test that no orders are returned before anything is submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client, clean_restock_orders):
        """Test submitting a valid restocking order."""
        payload = {
            "items": [{"sku": "WDG-001", "quantity": 100}],
            "budget": 5000,
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == 5000
        assert len(order["items"]) == 1

        item = order["items"][0]
        assert item["sku"] == "WDG-001"
        assert item["name"] == "Industrial Widget Type A"
        assert item["quantity"] == 100
        assert item["unit_price"] == 24.99

    def test_restock_order_total_calculation(self, client, clean_restock_orders):
        """Test that the total is computed from server-side unit costs."""
        payload = {
            "items": [
                {"sku": "WDG-001", "quantity": 100},
                {"sku": "GSK-203", "quantity": 200},
            ],
            "budget": 10000,
        }
        order = client.post("/api/restock-orders", json=payload).json()

        expected = 100 * 24.99 + 200 * 12.75
        assert abs(order["total_value"] - expected) < 0.01

    def test_restock_order_lead_time_is_max_of_items(self, client, clean_restock_orders):
        """Test that the order lead time equals the slowest item's lead time."""
        # WDG-001 is 7 days, GSK-203 is 5 days, VLV-506 is 12 days
        payload = {
            "items": [
                {"sku": "WDG-001", "quantity": 10},
                {"sku": "GSK-203", "quantity": 10},
                {"sku": "VLV-506", "quantity": 1},
            ],
            "budget": 10000,
        }
        order = client.post("/api/restock-orders", json=payload).json()

        assert order["lead_time_days"] == 12
        assert [i["lead_time_days"] for i in order["items"]] == [7, 5, 12]

    def test_restock_order_expected_delivery_matches_lead_time(self, client, clean_restock_orders):
        """Test that expected delivery is the submitted date plus the lead time."""
        payload = {"items": [{"sku": "GSK-203", "quantity": 10}], "budget": 1000}
        order = client.post("/api/restock-orders", json=payload).json()

        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - submitted == timedelta(days=order["lead_time_days"])
        assert "T" in order["submitted_date"]

    def test_restock_order_over_budget_rejected(self, client, clean_restock_orders):
        """Test that an order costing more than the budget is rejected."""
        # 100 x 24.99 = 2499.00
        payload = {"items": [{"sku": "WDG-001", "quantity": 100}], "budget": 2000}
        response = client.post("/api/restock-orders", json=payload)

        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restock-orders").json() == []

    def test_restock_order_exactly_on_budget_accepted(self, client, clean_restock_orders):
        """Test that an order equal to the budget is allowed."""
        payload = {"items": [{"sku": "WDG-001", "quantity": 100}], "budget": 2499}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

    def test_restock_order_empty_items_rejected(self, client, clean_restock_orders):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"items": [], "budget": 1000})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_restock_order_unknown_sku_rejected(self, client, clean_restock_orders):
        """Test that an unknown SKU is rejected."""
        payload = {"items": [{"sku": "NOPE-999", "quantity": 5}], "budget": 1000}
        response = client.post("/api/restock-orders", json=payload)

        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    def test_restock_order_duplicate_sku_rejected(self, client, clean_restock_orders):
        """Test that the same SKU cannot appear twice in one order."""
        payload = {
            "items": [
                {"sku": "WDG-001", "quantity": 5},
                {"sku": "WDG-001", "quantity": 5},
            ],
            "budget": 1000,
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_restock_order_non_positive_quantity_rejected(self, client, clean_restock_orders, quantity):
        """Test that zero or negative quantities fail validation."""
        payload = {"items": [{"sku": "WDG-001", "quantity": quantity}], "budget": 1000}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 422

    def test_restock_order_negative_budget_rejected(self, client, clean_restock_orders):
        """Test that a negative budget fails validation."""
        payload = {"items": [{"sku": "WDG-001", "quantity": 1}], "budget": -1}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 422

    def test_restock_order_missing_fields_rejected(self, client, clean_restock_orders):
        """Test that a request without a budget fails validation."""
        response = client.post("/api/restock-orders", json={"items": []})
        assert response.status_code == 422

    def test_get_restock_orders_lists_submitted_orders_newest_first(self, client, clean_restock_orders):
        """Test that submitted orders are listed, newest first, with unique numbers."""
        first = client.post(
            "/api/restock-orders",
            json={"items": [{"sku": "GSK-203", "quantity": 10}], "budget": 1000},
        ).json()
        second = client.post(
            "/api/restock-orders",
            json={"items": [{"sku": "FLT-405", "quantity": 10}], "budget": 1000},
        ).json()

        assert first["order_number"] != second["order_number"]

        response = client.get("/api/restock-orders")
        assert response.status_code == 200

        data = response.json()
        assert [o["order_number"] for o in data] == [
            second["order_number"],
            first["order_number"],
        ]

    def test_restock_orders_do_not_appear_in_customer_orders(self, client, clean_restock_orders):
        """Test that restock orders stay separate from /api/orders."""
        before = len(client.get("/api/orders").json())
        client.post(
            "/api/restock-orders",
            json={"items": [{"sku": "GSK-203", "quantity": 10}], "budget": 1000},
        )
        after = len(client.get("/api/orders").json())
        assert before == after
