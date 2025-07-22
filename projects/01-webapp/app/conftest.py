"""
Test configuration file for pytest.
This file sets up the test database, fixtures, and shared test utilities.
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from src.database import Base, Database
from src.auth.models import User
from src.task.models import Task
from src.auth.security import get_password_hash
from datetime import date
from main import app


@pytest.fixture(scope="function")
def test_db():
    """
    Create a temporary SQLite database for each test.
    This ensures complete isolation between tests.
    """
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # Create database connection
    test_db_url = f"sqlite:///{db_path}"
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create Database instance
    test_database = Database(test_db_url)
    test_database.engine = test_engine
    test_database.session = TestingSessionLocal

    yield test_database

    # Cleanup: Close connections and delete the temporary database file
    test_engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Create a database session for testing.
    """
    session = test_db.session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db, db_session):
    """
    Create a test client with dependency override for the database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override the database dependency
    app.dependency_overrides[test_db.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Create a test user in the database.
    """
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "full_name": "Test User",
        "hashed_password": get_password_hash("testpassword"),
        "disabled": False,
        "is_admin": False,
        "creation_date": date.today()
    }

    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin_user(db_session):
    """
    Create a test admin user in the database.
    """
    admin_data = {
        "username": "adminuser",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": get_password_hash("adminpassword"),
        "disabled": False,
        "is_admin": True,
        "creation_date": date.today()
    }

    admin = User(**admin_data)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def test_task(db_session, test_user):
    """
    Create a test task in the database.
    """
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "done": False,
        "user_id": test_user.id,
        "creation_date": date.today()
    }

    task = Task(**task_data)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """
    Create authentication headers for API requests.
    """
    login_data = {
        "username": test_user.username,
        "password": "testpassword"
    }

    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    token = token_data["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(client, test_admin_user):
    """
    Create authentication headers for admin API requests.
    """
    login_data = {
        "username": test_admin_user.username,
        "password": "adminpassword"
    }

    response = client.post("/api/auth/token", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    token = token_data["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_tasks(db_session, test_user):
    """
    Create multiple sample tasks for testing.
    """
    tasks = []
    for i in range(3):
        task = Task(
            title=f"Task {i+1}",
            description=f"Description for task {i+1}",
            done=i % 2 == 0,  # Alternate between done and not done
            user_id=test_user.id,
            creation_date=date.today()
        )
        db_session.add(task)
        tasks.append(task)

    db_session.commit()
    for task in tasks:
        db_session.refresh(task)

    return tasks


# Test environment variables
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """
    Set up test environment variables.
    This fixture runs automatically for all tests.
    """
    # Override environment variables for testing
    monkeypatch.setenv("db_connection", "sqlite:///./test.db")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_for_testing_only")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
