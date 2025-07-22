"""
Unit tests for task operations.
Tests the task CRUD operations, permissions, and business logic.
"""
import pytest
from datetime import date
from src.task.models import Task
from src.task.task import get_task, create_task, complete_task, update_task, delete_task
from src.task.schemas import TaskCreate
from src import exceptions


class TestTaskOperations:
    """Test class for task-related operations."""

    @pytest.mark.asyncio
    async def test_get_tasks_for_regular_user(self, db_session, test_user, sample_tasks):
        """Test that regular users only see their own tasks."""
        tasks = await get_task(db_session, test_user)

        assert len(tasks) == 3
        for task in tasks:
            assert task.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_tasks_for_admin_user(self, db_session, test_admin_user, sample_tasks):
        """Test that admin users can see all tasks."""
        tasks = await get_task(db_session, test_admin_user)

        assert len(tasks) == 3  # All tasks created by sample_tasks fixture

    @pytest.mark.asyncio
    async def test_create_task(self, db_session, test_user):
        """Test creating a new task."""
        task_data = TaskCreate(
            title="New Test Task",
            description="A new task for testing",
            done=False
        )

        created_task = await create_task(task_data, db_session, test_user)

        assert created_task.id is not None
        assert created_task.title == "New Test Task"
        assert created_task.description == "A new task for testing"
        assert created_task.done is False
        assert created_task.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_complete_task_by_owner(self, db_session, test_user, test_task):
        """Test that task owner can complete their task."""
        # Initially the task should not be done
        assert test_task.done is False

        result = await complete_task(test_task.id, db_session, test_user)

        assert result is True

        # Refresh task from database
        db_session.refresh(test_task)
        assert test_task.done is True

    @pytest.mark.asyncio
    async def test_complete_task_by_admin(self, db_session, test_admin_user, test_task):
        """Test that admin can complete any task."""
        assert test_task.done is False

        result = await complete_task(test_task.id, db_session, test_admin_user)

        assert result is True
        db_session.refresh(test_task)
        assert test_task.done is True

    @pytest.mark.asyncio
    async def test_complete_task_by_non_owner(self, db_session, test_user, test_task):
        """Test that non-owner cannot complete task."""
        # Create another user
        from src.auth.models import User
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

        with pytest.raises(exceptions.UserNotOwner):
            await complete_task(test_task.id, db_session, other_user)

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self, db_session, test_user):
        """Test completing a task that doesn't exist."""
        with pytest.raises(exceptions.TaskNotFound):
            await complete_task(999999, db_session, test_user)

    @pytest.mark.asyncio
    async def test_update_task_by_owner(self, db_session, test_user, test_task):
        """Test updating task by owner."""
        update_data = TaskCreate(
            title="Updated Task Title",
            description="Updated description",
            done=True
        )

        updated_task = await update_task(test_task.id, update_data, db_session, test_user)

        assert updated_task.title == "Updated Task Title"
        assert updated_task.done is True

    @pytest.mark.asyncio
    async def test_update_task_by_admin(self, db_session, test_admin_user, test_task):
        """Test updating task by admin."""
        update_data = TaskCreate(
            title="Admin Updated Task",
            description="Updated by admin",
            done=True
        )

        updated_task = await update_task(test_task.id, update_data, db_session, test_admin_user)

        assert updated_task.title == "Admin Updated Task"

    @pytest.mark.asyncio
    async def test_update_task_by_non_owner(self, db_session, test_user, test_task):
        """Test that non-owner cannot update task."""
        # Create another user
        from src.auth.models import User
        from src.auth.security import get_password_hash

        other_user = User(
            username="anotheruser",
            email="another@example.com",
            full_name="Another User",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )
        db_session.add(other_user)
        db_session.commit()

        update_data = TaskCreate(
            title="Unauthorized Update",
            description="This should fail",
            done=True
        )

        with pytest.raises(exceptions.UserNotOwner):
            await update_task(test_task.id, update_data, db_session, other_user)

    @pytest.mark.asyncio
    async def test_delete_task_by_owner(self, db_session, test_user, test_task):
        """Test deleting task by owner."""
        task_id = test_task.id

        result = await delete_task(task_id, db_session, test_user)

        assert result is True

        # Verify task is deleted
        deleted_task = db_session.query(Task).filter(Task.id == task_id).first()
        assert deleted_task is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(self, db_session, test_user):
        """Test deleting a task that doesn't exist."""
        with pytest.raises(exceptions.TaskNotFound):
            await delete_task(999999, db_session, test_user)


class TestTaskModel:
    """Test class for Task model."""

    def test_task_creation(self, db_session, test_user):
        """Test creating a task model directly."""
        task = Task(
            title="Direct Model Task",
            description="Created directly via model",
            done=False,
            user_id=test_user.id,
            creation_date=date.today()
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.id is not None
        assert task.title == "Direct Model Task"
        assert task.user_id == test_user.id

    def test_task_relationship(self, db_session, test_user, test_task):
        """Test that task-user relationship works correctly."""
        assert test_task.user is not None
        assert test_task.user.id == test_user.id
        assert test_task.user.username == test_user.username

    def test_task_query_by_user(self, db_session, test_user, sample_tasks):
        """Test querying tasks by user."""
        user_tasks = db_session.query(Task).filter(Task.user_id == test_user.id).all()

        assert len(user_tasks) == 3
        for task in user_tasks:
            assert task.user_id == test_user.id
