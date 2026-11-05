"""
Tests for task and purchase order endpoints.
"""
import pytest

from main import tasks, purchase_orders


@pytest.fixture(autouse=True)
def reset_state():
    """Each test starts with no tasks and no purchase orders."""
    tasks.clear()
    purchase_orders.clear()
    yield
    tasks.clear()
    purchase_orders.clear()


NEW_TASK = {"title": "Count Tokyo stock", "priority": "high", "dueDate": "2025-10-20"}

NEW_PO = {
    "backlog_item_id": "1",
    "supplier_name": "Acme Filters",
    "quantity": 350,
    "unit_cost": 12.5,
    "expected_delivery_date": "2025-11-01",
}


class TestTaskEndpoints:
    """Test suite for task endpoints."""

    def test_tasks_start_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        response = client.post("/api/tasks", json=NEW_TASK)
        assert response.status_code == 200
        task = response.json()
        assert task["id"]
        assert task["status"] == "pending"
        assert {k: task[k] for k in NEW_TASK} == NEW_TASK
        assert client.get("/api/tasks").json() == [task]

    def test_newest_task_first(self, client):
        client.post("/api/tasks", json=NEW_TASK)
        second = client.post("/api/tasks", json={**NEW_TASK, "title": "Second"}).json()
        assert client.get("/api/tasks").json()[0] == second

    def test_create_task_missing_field(self, client):
        response = client.post("/api/tasks", json={"title": "No date", "priority": "low"})
        assert response.status_code == 422

    def test_toggle_task(self, client):
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_task(self, client):
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_unknown_task(self, client, method):
        response = getattr(client, method)("/api/tasks/nope")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client):
        response = client.post("/api/purchase-orders", json=NEW_PO)
        assert response.status_code == 200
        po = response.json()
        assert po["id"]
        assert po["status"] == "Pending"
        assert po["created_date"]
        assert po["notes"] is None
        assert {k: po[k] for k in NEW_PO} == NEW_PO

    def test_get_purchase_order_by_backlog_item(self, client):
        created = client.post("/api/purchase-orders", json=NEW_PO).json()
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_backlog_flag_follows_purchase_order(self, client):
        def flag():
            backlog = client.get("/api/backlog").json()
            return next(item for item in backlog if item["id"] == "1")["has_purchase_order"]

        assert flag() is False
        client.post("/api/purchase-orders", json=NEW_PO)
        assert flag() is True

    def test_unknown_backlog_item(self, client):
        response = client.post("/api/purchase-orders", json={**NEW_PO, "backlog_item_id": "nope"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Backlog item not found"

    def test_no_purchase_order_for_backlog_item(self, client):
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert response.json()["detail"] == "Purchase order not found"
