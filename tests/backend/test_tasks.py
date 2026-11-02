"""
Tests for task API endpoints.
"""
import pytest


NEW_TASK = {"title": "Review supplier contracts", "priority": "high", "dueDate": "2025-10-20"}


class TestTasksEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty(self, client, clean_tasks):
        """Test that there are no API tasks by default."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client, clean_tasks):
        """Test creating a task returns it with a string id and pending status."""
        response = client.post("/api/tasks", json=NEW_TASK)
        assert response.status_code == 201

        task = response.json()
        assert isinstance(task["id"], str)
        assert task["title"] == NEW_TASK["title"]
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-20"
        assert task["status"] == "pending"

    def test_create_task_trims_title(self, client, clean_tasks):
        """Test that surrounding whitespace is stripped from the title."""
        response = client.post("/api/tasks", json={**NEW_TASK, "title": "  Padded  "})
        assert response.status_code == 201
        assert response.json()["title"] == "Padded"

    def test_create_task_defaults_priority(self, client, clean_tasks):
        """Test that priority defaults to medium."""
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2025-10-20"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_task_blank_title(self, client, clean_tasks):
        """Test that a whitespace-only title is rejected."""
        response = client.post("/api/tasks", json={**NEW_TASK, "title": "   "})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_task_invalid_priority(self, client, clean_tasks):
        """Test that an unknown priority is rejected."""
        response = client.post("/api/tasks", json={**NEW_TASK, "priority": "urgent"})
        assert response.status_code == 422

    def test_create_task_invalid_due_date(self, client, clean_tasks):
        """Test that a malformed due date is rejected."""
        response = client.post("/api/tasks", json={**NEW_TASK, "dueDate": "10/20/2025"})
        assert response.status_code == 400
        assert "dueDate" in response.json()["detail"]

    def test_create_task_missing_fields(self, client, clean_tasks):
        """Test that a missing due date is a validation error."""
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422

    def test_get_tasks_newest_first(self, client, clean_tasks):
        """Test that tasks are listed newest first."""
        first = client.post("/api/tasks", json={**NEW_TASK, "title": "First"}).json()
        second = client.post("/api/tasks", json={**NEW_TASK, "title": "Second"}).json()

        data = client.get("/api/tasks").json()
        assert [t["id"] for t in data] == [second["id"], first["id"]]

    def test_task_ids_are_unique_after_delete(self, client, clean_tasks):
        """Test that deleting a task never causes an id to be reused."""
        first = client.post("/api/tasks", json=NEW_TASK).json()
        second = client.post("/api/tasks", json=NEW_TASK).json()
        client.delete(f"/api/tasks/{first['id']}")
        third = client.post("/api/tasks", json=NEW_TASK).json()

        assert third["id"] not in (first["id"], second["id"])

    def test_toggle_task(self, client, clean_tasks):
        """Test toggling a task flips between pending and completed."""
        task = client.post("/api/tasks", json=NEW_TASK).json()

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client, clean_tasks):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/nonexistent-task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task(self, client, clean_tasks):
        """Test deleting a task removes it from the list."""
        task = client.post("/api/tasks", json=NEW_TASK).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_delete_nonexistent_task(self, client, clean_tasks):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/nonexistent-task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
