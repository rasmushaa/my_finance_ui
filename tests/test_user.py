"""Basic tests for the user domain model."""

from __future__ import annotations

from src.core.user import User


def test_user_properties_and_auth_helpers() -> None:
    """User exposes role/token and login checks."""
    user = User(
        user_name="Test User",
        user_picture_url="https://example.com/pic.png",
        user_role="admin",
        encoded_jwt_token="token-123",
    )

    assert user.token == "token-123"
    assert user.role == "admin"
    assert user.is_logged_in() is True
    assert user.is_admin() is True


def test_user_not_logged_in_for_empty_token() -> None:
    """Empty token means not logged in."""
    user = User(
        user_name="Test User",
        user_picture_url="https://example.com/pic.png",
        user_role="user",
        encoded_jwt_token="",
    )

    assert user.is_logged_in() is False
    assert user.is_admin() is False
