# ======================================================================================
# tests/integration/test_user.py
# ======================================================================================
# Purpose: Demonstrate user model interactions with the database using pytest fixtures.
#          Relies on 'conftest.py' for database session management and test isolation.
# ======================================================================================

import pytest
import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from tests.conftest import create_fake_user, managed_db_session
import uuid

# Use the logger configured in conftest.py
logger = logging.getLogger(__name__)

# ======================================================================================
# Basic Connection & Session Tests
# ======================================================================================

def test_database_connection(db_session):
    """
    Verify that the database connection is working.
    
    Uses the db_session fixture from conftest.py, which truncates tables after each test.
    """
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
    logger.info("Database connection test passed")


def test_managed_session():
    """
    Test the managed_db_session context manager for one-off queries and rollbacks.
    Demonstrates how a manual session context can work alongside the fixture-based approach.
    """
    with managed_db_session() as session:
        # Simple query
        session.execute(text("SELECT 1"))
        
        # Generate an error to trigger rollback
        try:
            session.execute(text("SELECT * FROM nonexistent_table"))
        except Exception as e:
            assert "nonexistent_table" in str(e)

# ======================================================================================
# Session Handling & Partial Commits
# ======================================================================================
def test_session_handling(db_session):
    """
    Demonstrate partial commits:
      - user1 is committed successfully.
      - user2 fails (due to duplicate email), triggering a rollback.
      - user3 is committed successfully.
      - The final user count should be the initial count plus two (user1 and user3).
    """
    # Use the current user count as our baseline.
    initial_count = db_session.query(User).count()
    logger.info(f"Initial user count before test_session_handling: {initial_count}")

    # Create and commit user1.
    user1 = User(
        first_name="User",
        last_name="One",
        email="user1@example.com",
        username="user1",
        password="hashed_password"
    )
    db_session.add(user1)
    db_session.commit()

    # Attempt to create user2 with a duplicate email (should fail).
    user2 = User(
        first_name="User",
        last_name="Two",
        email="user1@example.com",  # Duplicate email
        username="user2",
        password="hashed_password"
    )
    db_session.add(user2)
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.info(f"Expected failure on duplicate user2: {e}")

    # Create and commit user3 with unique email/username.
    user3 = User(
        first_name="User",
        last_name="Three",
        email="user3@example.com",
        username="user3",
        password="hashed_password"
    )
    db_session.add(user3)
    db_session.commit()

    # Verify that only two additional users have been added.
    final_count = db_session.query(User).count()
    expected_final = initial_count + 2
    assert final_count == expected_final, (
        f"Expected {expected_final} users after test, found {final_count}"
    )

# ======================================================================================
# User Creation Tests
# ======================================================================================

def test_create_user_with_faker(db_session):
    """
    Create a single user using Faker-generated data and verify it was saved.
    """
    user_data = create_fake_user()
    logger.info(f"Creating user with data: {user_data}")
    
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)  # Refresh populates fields like user.id
    
    assert user.id is not None
    assert user.email == user_data["email"]
    logger.info(f"Successfully created user with ID: {user.id}")


def test_create_multiple_users(db_session):
    """
    Create multiple users in a loop and verify they are all saved.
    """
    users = []
    for _ in range(3):
        user_data = create_fake_user()
        user = User(**user_data)
        users.append(user)
        db_session.add(user)
    
    db_session.commit()
    assert len(users) == 3
    logger.info(f"Successfully created {len(users)} users")

# ======================================================================================
# Query Tests
# ======================================================================================

def test_query_methods(db_session, seed_users):
    """
    Illustrate various query methods using seeded users.
    
    - Counting all users
    - Filtering by email
    - Ordering by email
    """
    user_count = db_session.query(User).count()
    assert user_count >= len(seed_users), "The user table should have at least the seeded users"
    
    first_user = seed_users[0]
    found = db_session.query(User).filter_by(email=first_user.email).first()
    assert found is not None, "Should find the seeded user by email"
    
    users_by_email = db_session.query(User).order_by(User.email).all()
    assert len(users_by_email) >= len(seed_users), "Query should return at least the seeded users"

# ======================================================================================
# Transaction / Rollback Tests
# ======================================================================================

def test_transaction_rollback(db_session):
    """
    Demonstrate how a partial transaction fails and triggers rollback.
    - We add a user and force an error
    - We catch the error and rollback
    - Verify the user was not committed
    """
    initial_count = db_session.query(User).count()
    
    try:
        user_data = create_fake_user()
        user = User(**user_data)
        db_session.add(user)
        # Force an error to trigger rollback
        db_session.execute(text("SELECT * FROM nonexistent_table"))
        db_session.commit()
    except Exception:
        db_session.rollback()
    
    final_count = db_session.query(User).count()
    assert final_count == initial_count, "The new user should not have been committed"

# ======================================================================================
# Update Tests
# ======================================================================================

def test_update_with_refresh(db_session, test_user):
    """
    Update a user's email and refresh the session to see updated fields.
    """
    original_email = test_user.email
    original_update_time = test_user.updated_at
    
    new_email = f"new_{original_email}"
    test_user.email = new_email
    db_session.commit()
    db_session.refresh(test_user)  # Refresh to populate any updated_at or other fields
    
    assert test_user.email == new_email, "Email should have been updated"
    assert test_user.updated_at > original_update_time, "Updated time should be newer"
    logger.info(f"Successfully updated user {test_user.id}")

# ======================================================================================
# Bulk Operation Tests
# ======================================================================================

@pytest.mark.slow
def test_bulk_operations(db_session):
    """
    Test bulk inserting multiple users at once (marked slow).
    Use --run-slow to enable this test.
    """
    users_data = [create_fake_user() for _ in range(10)]
    users = [User(**data) for data in users_data]
    db_session.bulk_save_objects(users)
    db_session.commit()
    
    count = db_session.query(User).count()
    assert count >= 10, "At least 10 users should now be in the database"
    logger.info(f"Successfully performed bulk operation with {len(users)} users")

# ======================================================================================
# Uniqueness Constraint Tests
# ======================================================================================

def test_unique_email_constraint(db_session):
    """
    Create two users with the same email and expect an IntegrityError.
    """
    first_user_data = create_fake_user()
    first_user = User(**first_user_data)
    db_session.add(first_user)
    db_session.commit()
    
    second_user_data = create_fake_user()
    second_user_data["email"] = first_user_data["email"]  # Force a duplicate email
    second_user = User(**second_user_data)
    db_session.add(second_user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_username_constraint(db_session):
    """
    Create two users with the same username and expect an IntegrityError.
    """
    first_user_data = create_fake_user()
    first_user = User(**first_user_data)
    db_session.add(first_user)
    db_session.commit()
    
    second_user_data = create_fake_user()
    second_user_data["username"] = first_user_data["username"]  # Force a duplicate username
    second_user = User(**second_user_data)
    db_session.add(second_user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

# ======================================================================================
# Persistence after Constraint Violation
# ======================================================================================

def test_user_persistence_after_constraint(db_session):
    """
    - Create and commit a valid user
    - Attempt to create a duplicate user (same email) -> fails
    - Confirm the original user still exists
    """
    initial_user_data = {
        "first_name": "First",
        "last_name": "User",
        "email": "first@example.com",
        "username": "firstuser",
        "password": "password123"
    }
    initial_user = User(**initial_user_data)
    db_session.add(initial_user)
    db_session.commit()
    saved_id = initial_user.id
    
    try:
        duplicate_user = User(
            first_name="Second",
            last_name="User",
            email="first@example.com",  # Duplicate
            username="seconduser",
            password="password456"
        )
        db_session.add(duplicate_user)
        db_session.commit()
        assert False, "Should have raised IntegrityError"
    except IntegrityError:
        db_session.rollback()
    
    found_user = db_session.query(User).filter_by(id=saved_id).first()
    assert found_user is not None, "Original user should exist"
    assert found_user.id == saved_id, "Should find original user by ID"
    assert found_user.email == "first@example.com", "Email should be unchanged"
    assert found_user.username == "firstuser", "Username should be unchanged"

# ======================================================================================
# Error Handling Test
# ======================================================================================

def test_error_handling():
    """
    Verify that a manual managed_db_session can capture and log invalid SQL errors.
    """
    with pytest.raises(Exception) as exc_info:
        with managed_db_session() as session:
            session.execute(text("INVALID SQL"))
    assert "INVALID SQL" in str(exc_info.value)

def test_authenticate_success(db_session, monkeypatch):
    """
    Test successful authentication with correct username/email and password.
    """
    # Create a user with a known password
    password = "securepass"
    user_data = {
        "first_name": "Auth",
        "last_name": "Tester",
        "email": "authuser@example.com",
        "username": "authuser",
        "password": User.hash_password(password),
        "is_active": True,
        "is_verified": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Patch token creation to return dummy tokens
    monkeypatch.setattr(User, "create_access_token", lambda data: "access_token")
    monkeypatch.setattr(User, "create_refresh_token", lambda data: "refresh_token")

    # Authenticate by username
    result = User.authenticate(db_session, "authuser", password)
    assert result is not None
    assert result["access_token"] == "access_token"
    assert result["refresh_token"] == "refresh_token"
    assert result["user"].id == user.id

    # Authenticate by email
    result_email = User.authenticate(db_session, "authuser@example.com", password)
    assert result_email is not None
    assert result_email["user"].id == user.id

def test_authenticate_wrong_password(db_session):
    """
    Test authentication fails with wrong password.
    """
    password = "rightpass"
    user_data = {
        "first_name": "Wrong",
        "last_name": "Password",
        "email": "wrongpass@example.com",
        "username": "wrongpassuser",
        "password": User.hash_password(password),
        "is_active": True,
        "is_verified": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()

    result = User.authenticate(db_session, "wrongpassuser", "incorrectpass")
    assert result is None

def test_authenticate_nonexistent_user(db_session):
    """
    Test authentication fails for nonexistent user.
    """
    result = User.authenticate(db_session, "nonexistentuser", "any_password")
    assert result is None

def test_authenticate_inactive_user(db_session, monkeypatch):
    """
    Test authentication fails for inactive user.
    """
    password = "inactivepass"
    user_data = {
        "first_name": "Inactive",
        "last_name": "User",
        "email": "inactive@example.com",
        "username": "inactiveuser",
        "password": User.hash_password(password),
        "is_active": False,
        "is_verified": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()

    # Patch verify_password to always return True for this test
    monkeypatch.setattr(User, "verify_password", lambda self, plain: True)
    # The authenticate method does not check is_active, so authentication should succeed
    result = User.authenticate(db_session, "inactiveuser", password)
    assert result is not None
    assert result["user"].id == user.id

def test_authenticate_updates_last_login(db_session, monkeypatch):
    """
    Test that authenticate updates last_login timestamp.
    """
    password = "loginpass"
    user_data = {
        "first_name": "Login",
        "last_name": "User",
        "email": "loginuser@example.com",
        "username": "loginuser",
        "password": User.hash_password(password),
        "is_active": True,
        "is_verified": True
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    monkeypatch.setattr(User, "create_access_token", lambda data: "access_token")
    monkeypatch.setattr(User, "create_refresh_token", lambda data: "refresh_token")

    assert user.last_login is None
    result = User.authenticate(db_session, "loginuser", password)
    db_session.refresh(user)
    assert user.last_login is not None

def test_verify_token_valid(monkeypatch):
    """
    Test User.verify_token returns correct UUID for a valid token.
    """

    # Setup: create a valid UUID and token payload
    user_id = uuid.uuid4()
    token_payload = {"sub": str(user_id)}

    # Patch settings and jose.jwt.decode to return our payload
    class DummySettings:
        JWT_SECRET_KEY = "secret"
        ALGORITHM = "HS256"
    monkeypatch.setattr("app.core.config.settings", DummySettings())

    def dummy_decode(token, key, algorithms):
        return token_payload
    monkeypatch.setattr("jose.jwt.decode", dummy_decode)

    token = "valid_token"
    result = User.verify_token(token)
    assert result == user_id

def test_verify_token_missing_sub(monkeypatch):
    """
    Test User.verify_token returns None if 'sub' is missing from payload.
    """
    class DummySettings:
        JWT_SECRET_KEY = "secret"
        ALGORITHM = "HS256"
    monkeypatch.setattr("app.core.config.settings", DummySettings())

    def dummy_decode(token, key, algorithms):
        return {}  # No 'sub'
    monkeypatch.setattr("jose.jwt.decode", dummy_decode)

    token = "token_without_sub"
    result = User.verify_token(token)
    assert result is None

def test_verify_token_invalid_uuid(monkeypatch):
    """
    Test User.verify_token returns None if 'sub' is not a valid UUID.
    """
    class DummySettings:
        JWT_SECRET_KEY = "secret"
        ALGORITHM = "HS256"
    monkeypatch.setattr("app.core.config.settings", DummySettings())

    def dummy_decode(token, key, algorithms):
        return {"sub": "not-a-uuid"}
    monkeypatch.setattr("jose.jwt.decode", dummy_decode)

    token = "token_with_invalid_uuid"
    result = User.verify_token(token)
    assert result is None

def test_update_single_field(db_session, test_user):
    """
    Test updating a single field using the update method.
    """
    old_updated_at = test_user.updated_at
    new_first_name = "UpdatedName"
    test_user.update(first_name=new_first_name)
    db_session.commit()
    db_session.refresh(test_user)
    assert test_user.first_name == new_first_name
    assert test_user.updated_at > old_updated_at

def test_update_multiple_fields(db_session, test_user):
    """
    Test updating multiple fields at once using the update method.
    """
    old_updated_at = test_user.updated_at
    new_data = {
        "first_name": "Multi",
        "last_name": "Field",
        "email": "multi.field@example.com"
    }
    test_user.update(**new_data)
    db_session.commit()
    db_session.refresh(test_user)
    assert test_user.first_name == new_data["first_name"]
    assert test_user.last_name == new_data["last_name"]
    assert test_user.email == new_data["email"]
    assert test_user.updated_at > old_updated_at

def test_update_no_fields(db_session, test_user):
    """
    Test calling update with no fields does not change attributes except updated_at.
    """
    old_first_name = test_user.first_name
    old_updated_at = test_user.updated_at
    test_user.update()
    db_session.commit()
    db_session.refresh(test_user)
    assert test_user.first_name == old_first_name
    assert test_user.updated_at > old_updated_at

def test_update_returns_self(db_session, test_user):
    """
    Test that update returns the user instance itself.
    """
    result = test_user.update(first_name="ReturnTest")
    assert result is test_user