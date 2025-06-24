"""
Pytest configuration file for Bible Database tests.

This file contains shared fixtures and configurations for the Bible Database
test suite.
"""


def pytest_configure(config):
    """Register custom markers for pytest."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require a real database connection"
    )
