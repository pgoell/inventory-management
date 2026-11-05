"""
Tests for reports API endpoints.
"""


def orders_total(client, query=""):
    orders = client.get(f"/api/orders{query}").json()
    return len(orders), sum(o["total_value"] for o in orders)


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test the unfiltered quarterly report shape and order."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert [q["quarter"] for q in data] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]
        for q in data:
            for field in ("total_orders", "total_revenue", "delivered_orders",
                          "avg_order_value", "fulfillment_rate"):
                assert field in q
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly totals add up to all orders."""
        data = client.get("/api/reports/quarterly").json()
        count, revenue = orders_total(client)
        assert sum(q["total_orders"] for q in data) == count
        assert abs(sum(q["total_revenue"] for q in data) - revenue) < 0.01

    def test_get_quarterly_reports_by_quarter(self, client):
        """Test that a quarter filter returns only that quarter."""
        data = client.get("/api/reports/quarterly?month=Q2-2025").json()
        assert [q["quarter"] for q in data] == ["Q2-2025"]

    def test_get_quarterly_reports_multiple_filters(self, client):
        """Test that warehouse, category and status filters match /api/orders."""
        query = "?warehouse=Tokyo&category=Sensors&status=Delivered"
        data = client.get(f"/api/reports/quarterly{query}").json()
        count, revenue = orders_total(client, query)
        assert sum(q["total_orders"] for q in data) == count
        assert abs(sum(q["total_revenue"] for q in data) - revenue) < 0.01
        for q in data:
            assert q["fulfillment_rate"] == 100.0


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test the unfiltered monthly trends shape and order."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        months = [m["month"] for m in data]
        assert len(months) == 12
        assert months == sorted(months)
        for m in data:
            for field in ("order_count", "revenue", "delivered_count"):
                assert field in m

    def test_get_monthly_trends_by_month(self, client):
        """Test that a month filter returns only that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-03").json()
        assert [m["month"] for m in data] == ["2025-03"]

    def test_get_monthly_trends_by_quarter(self, client):
        """Test that a quarter filter returns its three months."""
        data = client.get("/api/reports/monthly-trends?month=Q4-2025").json()
        assert [m["month"] for m in data] == ["2025-10", "2025-11", "2025-12"]

    def test_get_monthly_trends_by_warehouse(self, client):
        """Test that a warehouse filter matches /api/orders."""
        data = client.get("/api/reports/monthly-trends?warehouse=London").json()
        count, revenue = orders_total(client, "?warehouse=London")
        assert sum(m["order_count"] for m in data) == count
        assert abs(sum(m["revenue"] for m in data) - revenue) < 0.01

    def test_get_monthly_trends_no_match(self, client):
        """Test that filters matching nothing return an empty list."""
        response = client.get("/api/reports/monthly-trends?warehouse=Nowhere")
        assert response.status_code == 200
        assert response.json() == []
