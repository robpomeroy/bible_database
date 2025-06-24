#!/usr/bin/env python
"""
Example usage of the BibleDatabase class.
"""

from bible_db import BibleDatabase


def main():
    """
    Example of using the Bible Database client.
    """
    # Using context manager (automatically handles connection/disconnection)
    with BibleDatabase() as db:
        # Set log level to DEBUG for detailed SQL logging
        db.set_log_level("DEBUG")

        # Example 1: Get John 3:16 from the KJV translation
        print("Example 1: John 3:16 (YLT)")
        print("=" * 50)

        verses = db.get_verses(ref="John 3:16", translation="YLT")

        for verse in verses:
            print(
                f"{verse['chapter']}:{verse['verse']} - {verse['text']}"
            )

        print("\n")

        # Example 2: List available translations
        print("Example 2: Available Translations")
        print("=" * 50)
        translations = db.get_available_translations()
        if translations:
            for t in translations:
                print(f"{t['table']} - {t['version']}")
        else:
            print("No translations found or not connected to the database.")


if __name__ == "__main__":
    main()
