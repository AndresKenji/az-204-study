"""
Database integration tests.
Tests database connections, migrations, and model relationships.
"""
import pytest
from sqlalchemy import text
from src.database import Base
from src.auth.models import User
from src.task.models import Task
from datetime import date


class TestDatabaseConnection:
    """Test class for database connectivity and basic operations."""

    def test_database_connection(self, test_db):
        """Test that database connection works."""
        with test_db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1

    def test_database_tables_exist(self, test_db):
        """Test that all required tables are created."""
        inspector = test_db.engine.dialect.get_table_names(test_db.engine.connect())

        expected_tables = ["user", "task"]
        for table in expected_tables:
            assert table in inspector

    def test_database_session_creation(self, db_session):
        """Test that database session can be created."""
        assert db_session is not None

        # Test simple query
        result = db_session.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1

    def test_database_transaction_rollback(self, db_session):
        """Test that database transactions can be rolled back."""
        # Create a user
        user = User(
            username="rollback_test",
            email="rollback@example.com",
            full_name="Rollback Test",
            hashed_password="hashed",
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )

        db_session.add(user)
        db_session.flush()  # Flush but don't commit

        # User should exist in session
        found_user = db_session.query(User).filter(User.username == "rollback_test").first()
        assert found_user is not None

        # Rollback transaction
        db_session.rollback()

        # User should no longer exist
        found_user = db_session.query(User).filter(User.username == "rollback_test").first()
        assert found_user is None

    def test_database_isolation_between_tests(self, db_session):
        """Test that each test gets a clean database."""
        # This user should not exist from other tests
        existing_user = db_session.query(User).filter(User.username == "isolation_test").first()
        assert existing_user is None

        # Create user
        user = User(
            username="isolation_test",
            email="isolation@example.com",
            full_name="Isolation Test",
            hashed_password="hashed",
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )

        db_session.add(user)
        db_session.commit()

        # User should exist now
        found_user = db_session.query(User).filter(User.username == "isolation_test").first()
        assert found_user is not None


class TestModelRelationships:
    """Test class for model relationships and foreign keys."""

    def test_user_task_relationship(self, db_session, test_user):
        """Test the relationship between User and Task models."""
        # Create tasks for the user
        task1 = Task(
            title="Relationship Test 1",
            description="Test task 1",
            done=False,
            user_id=test_user.id,
            creation_date=date.today()
        )

        task2 = Task(
            title="Relationship Test 2",
            description="Test task 2",
            done=True,
            user_id=test_user.id,
            creation_date=date.today()
        )

        db_session.add_all([task1, task2])
        db_session.commit()

        # Refresh user to load relationships
        db_session.refresh(test_user)

        # Test forward relationship (User -> Tasks)
        assert len(test_user.tasks) >= 2  # At least these 2 tasks
        task_titles = [task.title for task in test_user.tasks]
        assert "Relationship Test 1" in task_titles
        assert "Relationship Test 2" in task_titles

        # Test backward relationship (Task -> User)
        assert task1.user.id == test_user.id
        assert task1.user.username == test_user.username
        assert task2.user.id == test_user.id

    def test_foreign_key_constraint(self, db_session):
        """Test that foreign key constraints are enforced."""
        # Try to create a task with invalid user_id
        invalid_task = Task(
            title="Invalid FK Test",
            description="This should fail",
            done=False,
            user_id=99999,  # Non-existent user ID
            creation_date=date.today()
        )

        db_session.add(invalid_task)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_cascade_delete_behavior(self, db_session):
        """Test cascade delete behavior (if configured)."""
        # Create user and task
        user = User(
            username="cascade_test",
            email="cascade@example.com",
            full_name="Cascade Test",
            hashed_password="hashed",
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        task = Task(
            title="Will be orphaned",
            description="Test cascade",
            done=False,
            user_id=user.id,
            creation_date=date.today()
        )
        db_session.add(task)
        db_session.commit()
        task_id = task.id

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Check what happens to the task
        remaining_task = db_session.query(Task).filter(Task.id == task_id).first()
        # Depending on your cascade configuration, task might be deleted or remain
        # This test documents the current behavior
        # If tasks should be deleted when user is deleted, assert remaining_task is None
        # If tasks should remain as orphans, assert remaining_task is not None


class TestDatabasePerformance:
    """Test class for database performance considerations."""

    def test_query_efficiency(self, db_session, test_user):
        """Test query efficiency and N+1 problems."""
        # Create multiple tasks
        tasks = []
        for i in range(10):
            task = Task(
                title=f"Performance Test {i}",
                description=f"Task {i}",
                done=i % 2 == 0,
                user_id=test_user.id,
                creation_date=date.today()
            )
            tasks.append(task)

        db_session.add_all(tasks)
        db_session.commit()

        # Test efficient querying with joins
        from sqlalchemy.orm import joinedload

        user_with_tasks = db_session.query(User).options(
            joinedload(User.tasks)
        ).filter(User.id == test_user.id).first()

        assert user_with_tasks is not None
        assert len(user_with_tasks.tasks) >= 10

    def test_bulk_operations(self, db_session, test_user):
        """Test bulk database operations."""
        # Bulk insert
        tasks_data = []
        for i in range(100):
            tasks_data.append({
                "title": f"Bulk Task {i}",
                "description": f"Bulk description {i}",
                "done": False,
                "user_id": test_user.id,
                "creation_date": date.today()
            })

        db_session.bulk_insert_mappings(Task, tasks_data)
        db_session.commit()

        # Verify insertion
        task_count = db_session.query(Task).filter(Task.user_id == test_user.id).count()
        assert task_count >= 100

    def test_connection_handling(self, test_db):
        """Test proper connection handling."""
        # Test that connections are properly managed
        initial_connections = test_db.engine.pool.size()

        # Create multiple sessions
        sessions = []
        for _ in range(5):
            session = test_db.session()
            sessions.append(session)
            # Perform a simple query
            session.execute(text("SELECT 1")).fetchone()

        # Close all sessions
        for session in sessions:
            session.close()

        # Connection pool should return to normal
        final_connections = test_db.engine.pool.size()
        assert final_connections == initial_connections
