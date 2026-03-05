"""Pytest configuration and shared fixtures."""
import pytest
import os


@pytest.fixture(autouse=True)
def set_admin_token():
    """Set ADMIN_TOKEN for all tests."""
    os.environ["ADMIN_TOKEN"] = "test-token"
    yield
    os.environ.pop("ADMIN_TOKEN", None)
