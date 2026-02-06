import pytest
from unittest.mock import patch
from src.auth.models import User


@pytest.fixture(autouse=True)
def mock_password_hashing():
    with patch("src.auth.models.hash_password") as mock_hash:
        mock_hash.side_effect = lambda p: f"hashed_{p}"
        yield


def test_create_user_hashes_password():
    user = User.create(
        email="test@example.com", raw_password="SafePassword123!", group_id=1
    )
    assert user.email == "test@example.com"
    assert "hashed_" in user.hashed_password


def test_password_strength_validation():
    user = User(email="test@test.com", group_id=1)

    with pytest.raises(ValueError):
        user.password = "123"


def test_user_repr():
    user = User(id=1, email="test@test.com", is_active=True)
    assert "test@test.com" in repr(user)
