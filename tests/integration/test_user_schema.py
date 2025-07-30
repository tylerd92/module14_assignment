import pytest
from pydantic import ValidationError
from app.schemas.user import PasswordUpdate, UserCreate

def test_password_update_success():
    """
    PasswordUpdate should succeed when new_password and confirm_new_password match,
    and new_password is different from current_password.
    """
    data = {
        "current_password": "OldPass123!",
        "new_password": "NewPass123!",
        "confirm_new_password": "NewPass123!"
    }
    obj = PasswordUpdate(**data)
    assert obj.new_password == obj.confirm_new_password
    assert obj.current_password != obj.new_password

def test_password_update_mismatch():
    """
    PasswordUpdate should raise ValidationError when new_password and confirm_new_password do not match.
    """
    data = {
        "current_password": "OldPass123!",
        "new_password": "NewPass123!",
        "confirm_new_password": "Mismatch123!"
    }
    with pytest.raises(ValidationError) as exc_info:
        PasswordUpdate(**data)
    assert "New password and confirmation do not match" in str(exc_info.value)

def test_password_update_same_as_current():
    """
    PasswordUpdate should raise ValidationError when new_password is the same as current_password.
    """
    data = {
        "current_password": "SamePass123!",
        "new_password": "SamePass123!",
        "confirm_new_password": "SamePass123!"
    }
    with pytest.raises(ValidationError) as exc_info:
        PasswordUpdate(**data)
    assert "New password must be different from current password" in str(exc_info.value)

def test_usercreate_passwords_match():
    """
    Test that UserCreate raises ValueError when passwords do not match.
    """

    valid_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }
    # Should not raise
    user = UserCreate(**valid_data)
    assert user.password == user.confirm_password

    # Should raise ValueError for mismatched passwords
    invalid_data = valid_data.copy()
    invalid_data["confirm_password"] = "DifferentPass123!"
    with pytest.raises(ValueError, match="Passwords do not match"):
        UserCreate(**invalid_data)

def test_usercreate_password_no_uppercase():
    """
    Test that UserCreate raises ValidationError when password does not contain an uppercase letter.
    """
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "securepass123!",
        "confirm_password": "securepass123!"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "Password must contain at least one uppercase letter" in str(exc_info.value)

def test_usercreate_password_no_lowercase():
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SECUREPASS123!",
        "confirm_password": "SECUREPASS123!"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "Password must contain at least one lowercase letter" in str(exc_info.value)

def test_usercreate_password_no_special_char():
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "Password must contain at least one special character" in str(exc_info.value)

def test_usercreate_password_no_digit():
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SecurePassword!",
        "confirm_password": "SecurePassword!"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "Password must contain at least one digit" in str(exc_info.value)

    