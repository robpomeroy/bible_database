#!/usr/bin/env python
"""
Test connectivity to the Bible Database.
"""

import logging
from bible_db import BibleDatabase

logging.basicConfig(level=logging.INFO)


def test_connection():
    """Test the database connection."""
    print("Testing Bible Database connection...")

    try:
        # Try to connect and verify schema
        with BibleDatabase() as db:
            # Check if we can connect
            print("✓ Connected to database")

            # Check if the bible_version_key table exists
            translations = db.get_available_translations()
            if translations:
                print(f"✓ Found {len(translations)} translations")
                print("Available translations:")
                for t in translations:
                    print(f"  • {t['table']} - {t['version']}")
            else:
                print("✗ No translations found - check database schema")

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

    return True


if __name__ == "__main__":
    test_connection()
