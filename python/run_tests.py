#!/usr/bin/env python
"""
Test runner script for bible_db.py

This script runs the test suite for the BibleDatabase class.
Run it with pytest arguments to customize test execution.

Examples:
    python run_tests.py              # Run all tests
    python run_tests.py -xvs         # Run with verbose output
    python run_tests.py -k "book"    # Run tests with "book" in the name
    python run_tests.py -m integration # Run only integration tests

Note: Integration tests require a valid database connection.
Edit .env.test to configure connection details and set
SKIP_DB_INTEGRATION_TESTS=false to run integration tests.
"""

import os
import sys
import pytest

if __name__ == "__main__":
    # Get command line arguments, or use defaults
    args = sys.argv[1:] if len(sys.argv) > 1 else ["-xvs"]

    try:
        import dotenv
        # Check if .env.test exists and has SKIP_DB_INTEGRATION_TESTS=false
        if os.path.exists(".env.test"):
            env_vars = dotenv.dotenv_values(".env.test")
            skip_value = env_vars.get("SKIP_DB_INTEGRATION_TESTS", "true")
            # Handle potential None value
            skip_tests = skip_value.lower() == "true" if skip_value else True

            # If not skipping integration tests and no specific marker provided
            has_marker = any(arg.startswith("-m") for arg in args)
            run_all = not skip_tests and not has_marker
            if run_all:
                print("Integration tests enabled - running all tests")
    except ImportError:
        pass  # If dotenv isn't available, just continue with normal args

    # Add the test file to args
    args.append("test_bible_db.py")

    # Run the tests
    exit_code = pytest.main(args)

    # Return the exit code
    sys.exit(exit_code)
