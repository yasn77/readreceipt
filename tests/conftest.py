"""Pytest configuration and shared fixtures."""
import pytest
import os


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables for all tests."""
    # Save original values
    original_admin_token = os.environ.get("ADMIN_TOKEN")
    original_db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI")

    # Set test values
    os.environ["ADMIN_TOKEN"] = "test-token"
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    yield

    # Restore original values
    if original_admin_token:
        os.environ["ADMIN_TOKEN"] = original_admin_token
    else:
        os.environ.pop("ADMIN_TOKEN", None)

    if original_db_uri:
        os.environ["SQLALCHEMY_DATABASE_URI"] = original_db_uri
    else:
        os.environ.pop("SQLALCHEMY_DATABASE_URI", None)
