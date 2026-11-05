"""
Tests for restocking order API endpoints.
"""


class TestRestockOrderEndpoints:
    """Test suite for restock order endpoints."""

    def test_demand_forecasts_have_cost_and_lead_time(self, client):
        """Test that every forecast carries a unit cost and lead time."""
        data = client.get("/api/demand").json()
        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0

    def test_create_restock_order(self, client):
        """Test submitting a restock order computes totals and delivery from forecasts."""
        response = client.post("/api/restock-orders", json={
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 150}, {"sku": "GSK-203", "quantity": 100}],
        })
        assert response.status_code == 201

        order = response.json()
        assert isinstance(order["id"], int)
        assert abs(order["total_cost"] - (150 * 18.5 + 100 * 6.75)) < 0.01
        assert order["lead_time_days"] == 14  # longest line: WDG-001
        assert len(order["expected_delivery"]) == 10  # YYYY-MM-DD
        names = {item["sku"]: item["name"] for item in order["items"]}
        assert names["WDG-001"] == "Industrial Widget Type A"

    def test_get_restock_orders_lists_submitted(self, client):
        """Test that a submitted order shows up in the list, newest first."""
        created = client.post("/api/restock-orders", json={
            "budget": 1000, "items": [{"sku": "FLT-405", "quantity": 10}],
        }).json()

        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["id"] == created["id"]
        assert data[0]["items"][0]["sku"] == "FLT-405"

    def test_create_restock_order_unknown_sku(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    def test_create_restock_order_non_positive_quantity(self, client):
        """Test that a zero quantity is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 1000, "items": [{"sku": "WDG-001", "quantity": 0}],
        })
        assert response.status_code == 400

    def test_create_restock_order_empty(self, client):
        """Test that an order without items is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_create_restock_order_over_budget(self, client):
        """Test that an order costing more than the budget is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 100, "items": [{"sku": "MTR-304", "quantity": 1}],
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
