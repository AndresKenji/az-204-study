"""
API integration tests for task endpoints.
Tests the FastAPI endpoints for task management.
"""
import pytest
from datetime import date


class TestTaskAPI:
    """Test class for task API endpoints."""

    def test_get_tasks_authenticated(self, client, auth_headers, sample_tasks):
        """Test getting tasks with authentication."""
        response = client.get("/api/task/", headers=auth_headers)

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3

        # Verify task structure
        for task in tasks:
            assert "id" in task
            assert "title" in task
            assert "done" in task
            assert "user_id" in task

    def test_get_tasks_unauthenticated(self, client):
        """Test getting tasks without authentication."""
        response = client.get("/api/task/")

        assert response.status_code == 401  # Unauthorized

    def test_get_tasks_admin_sees_all(self, client, admin_auth_headers, sample_tasks):
        """Test that admin users see all tasks."""
        response = client.get("/api/task/", headers=admin_auth_headers)

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3  # All tasks from sample_tasks

    def test_create_task_authenticated(self, client, auth_headers):
        """Test creating a task with authentication."""
        task_data = {
            "title": "API Test Task",
            "description": "Created via API",
            "done": False
        }

        response = client.post("/api/task/", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        created_task = response.json()
        assert created_task["title"] == "API Test Task"
        assert created_task["description"] == "Created via API"
        assert created_task["done"] is False

    def test_create_task_unauthenticated(self, client):
        """Test creating a task without authentication."""
        task_data = {
            "title": "Should Fail",
            "description": "No auth",
            "done": False
        }

        response = client.post("/api/task/", json=task_data)

        assert response.status_code == 401

    def test_create_task_invalid_data(self, client, auth_headers):
        """Test creating a task with invalid data."""
        task_data = {
            "description": "Missing title",  # Title is required
            "done": False
        }

        response = client.post("/api/task/", json=task_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_complete_task_by_owner(self, client, auth_headers, test_task):
        """Test completing a task by its owner."""
        response = client.get(f"/api/task/done/{test_task.id}", headers=auth_headers)

        assert response.status_code == 200

    def test_complete_task_by_admin(self, client, admin_auth_headers, test_task):
        """Test completing a task by admin."""
        response = client.get(f"/api/task/done/{test_task.id}", headers=admin_auth_headers)

        assert response.status_code == 200

    def test_complete_nonexistent_task(self, client, auth_headers):
        """Test completing a task that doesn't exist."""
        response = client.get("/api/task/done/999999", headers=auth_headers)

        assert response.status_code == 404

    def test_update_task_by_owner(self, client, auth_headers, test_task):
        """Test updating a task by its owner."""
        update_data = {
            "title": "Updated via API",
            "description": "Updated description",
            "done": True
        }

        response = client.put(f"/api/task/{test_task.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["title"] == "Updated via API"

    def test_update_task_unauthenticated(self, client, test_task):
        """Test updating a task without authentication."""
        update_data = {
            "title": "Should Fail",
            "description": "No auth",
            "done": True
        }

        response = client.put(f"/api/task/{test_task.id}", json=update_data)

        assert response.status_code == 401

    def test_delete_task_by_owner(self, client, auth_headers, test_task):
        """Test deleting a task by its owner."""
        response = client.delete(f"/api/task/{test_task.id}", headers=auth_headers)

        assert response.status_code == 200

    def test_delete_task_unauthenticated(self, client, test_task):
        """Test deleting a task without authentication."""
        response = client.delete(f"/api/task/{test_task.id}")

        assert response.status_code == 401

    def test_delete_nonexistent_task(self, client, auth_headers):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/task/999999", headers=auth_headers)

        assert response.status_code == 404


class TestTaskAPIPermissions:
    """Test class for task API permission checks."""

    def test_user_cannot_access_others_tasks(self, client, db_session, test_user, auth_headers):
        """Test that users cannot access tasks they don't own."""
        # Create another user and task
        from src.auth.models import User
        from src.task.models import Task
        from src.auth.security import get_password_hash

        other_user = User(
            username="otheruser",
            email="other@example.com",
            full_name="Other User",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_task = Task(
            title="Other User's Task",
            description="This belongs to another user",
            done=False,
            user_id=other_user.id,
            creation_date=date.today()
        )
        db_session.add(other_task)
        db_session.commit()
        db_session.refresh(other_task)

        # Try to complete other user's task
        response = client.get(f"/api/task/done/{other_task.id}", headers=auth_headers)
        assert response.status_code == 401

        # Try to update other user's task
        update_data = {
            "title": "Hacked",
            "description": "Should not work",
            "done": True
        }
        response = client.put(f"/api/task/{other_task.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 401

    def test_admin_can_access_all_tasks(self, client, admin_auth_headers, test_task):
        """Test that admin can access any task."""
        # Admin should be able to complete any task
        response = client.get(f"/api/task/done/{test_task.id}", headers=admin_auth_headers)
        assert response.status_code == 200

        # Admin should be able to update any task
        update_data = {
            "title": "Admin Updated",
            "description": "Updated by admin",
            "done": True
        }
        response = client.put(f"/api/task/{test_task.id}", json=update_data, headers=admin_auth_headers)
        assert response.status_code == 200


class TestTaskAPIValidation:
    """Test class for task API data validation."""

    def test_create_task_empty_title(self, client, auth_headers):
        """Test creating task with empty title."""
        task_data = {
            "title": "",  # Empty title
            "description": "Valid description",
            "done": False
        }

        response = client.post("/api/task/", json=task_data, headers=auth_headers)

        assert response.status_code == 422

    def test_create_task_missing_fields(self, client, auth_headers):
        """Test creating task with missing required fields."""
        task_data = {
            "done": False
            # Missing title and description
        }

        response = client.post("/api/task/", json=task_data, headers=auth_headers)

        assert response.status_code == 422

    def test_create_task_invalid_done_value(self, client, auth_headers):
        """Test creating task with invalid 'done' value."""
        task_data = {
            "title": "Valid Title",
            "description": "Valid description",
            "done": "not_a_boolean"  # Invalid boolean value
        }

        response = client.post("/api/task/", json=task_data, headers=auth_headers)

        assert response.status_code == 422
