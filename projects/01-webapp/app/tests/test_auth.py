"""
Unit tests for authentication and user operations.
Tests user creation, authentication, authorization, and user management.
"""
import pytest
from datetime import date
from src.auth.models import User
from src.auth.security import verify_password, get_password_hash, authenticate_user
from src import exceptions


class TestUserModel:
    """Test class for User model operations."""

    def test_user_creation(self, db_session):
        """Test creating a user model directly."""
        user = User(
            username="newuser",
            email="new@example.com",
            full_name="New User",
            hashed_password=get_password_hash("newpassword"),
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.disabled is False
        assert user.is_admin is False

    def test_user_unique_constraints(self, db_session, test_user):
        """Test that username and email must be unique."""
        # Try to create user with same username
        duplicate_username_user = User(
            username=test_user.username,  # Same username
            email="different@example.com",
            full_name="Different User",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )

        db_session.add(duplicate_username_user)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

        db_session.rollback()

        # Try to create user with same email
        duplicate_email_user = User(
            username="differentuser",
            email=test_user.email,  # Same email
            full_name="Different User",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_admin=False,
            creation_date=date.today()
        )

        db_session.add(duplicate_email_user)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password  # Password should be hashed
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_user_tasks_relationship(self, db_session, test_user, test_task):
        """Test that user-tasks relationship works correctly."""
        assert len(test_user.tasks) >= 1
        assert test_task in test_user.tasks


class TestAuthentication:
    """Test class for authentication operations."""

    def test_authenticate_user_success(self, test_db, test_user):
        """Test successful user authentication."""
        authenticated_user = authenticate_user(test_db, "testuser", "testpassword")

        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
        assert authenticated_user.id == test_user.id

    def test_authenticate_user_wrong_password(self, test_db, test_user):
        """Test authentication with wrong password."""
        authenticated_user = authenticate_user(test_db, "testuser", "wrongpassword")

        assert authenticated_user is False

    def test_authenticate_user_nonexistent(self, test_db):
        """Test authentication with nonexistent user."""
        authenticated_user = authenticate_user(test_db, "nonexistent", "password")

        assert authenticated_user is False

    def test_authenticate_disabled_user(self, test_db, db_session):
        """Test authentication with disabled user."""
        # Create disabled user
        disabled_user = User(
            username="disableduser",
            email="disabled@example.com",
            full_name="Disabled User",
            hashed_password=get_password_hash("password"),
            disabled=True,  # User is disabled
            is_admin=False,
            creation_date=date.today()
        )

        db_session.add(disabled_user)
        db_session.commit()

        authenticated_user = authenticate_user(test_db, "disableduser", "password")

        assert authenticated_user is False


class TestUserPermissions:
    """Test class for user permissions and authorization."""

    def test_admin_user_permissions(self, test_admin_user):
        """Test admin user has admin privileges."""
        assert test_admin_user.is_admin is True
        assert test_admin_user.disabled is False

    def test_regular_user_permissions(self, test_user):
        """Test regular user doesn't have admin privileges."""
        assert test_user.is_admin is False
        assert test_user.disabled is False

    def test_user_disable_functionality(self, db_session, test_user):
        """Test user can be disabled."""
        # Disable the user
        test_user.disabled = True
        test_user.disable_date = date.today()

        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        assert test_user.disabled is True
        assert test_user.disable_date is not None


class TestUserCreation:
    """Test class for user creation operations."""

    def test_create_regular_user(self, db_session):
        """Test creating a regular user."""
        user_data = {
            "username": "regularuser",
            "email": "regular@example.com",
            "full_name": "Regular User",
            "hashed_password": get_password_hash("regularpassword"),
            "disabled": False,
            "is_admin": False,
            "creation_date": date.today()
        }

        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.is_admin is False
        assert user.disabled is False

    def test_create_admin_user(self, db_session):
        """Test creating an admin user."""
        admin_data = {
            "username": "newadmin",
            "email": "newadmin@example.com",
            "full_name": "New Admin",
            "hashed_password": get_password_hash("adminpassword"),
            "disabled": False,
            "is_admin": True,
            "creation_date": date.today()
        }

        admin = User(**admin_data)
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

        assert admin.id is not None
        assert admin.is_admin is True
        assert admin.disabled is False

    def test_user_creation_date_set(self, db_session):
        """Test that creation date is properly set."""
        today = date.today()
        user = User(
            username="dateuser",
            email="date@example.com",
            full_name="Date User",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_admin=False,
            creation_date=today
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.creation_date == today
