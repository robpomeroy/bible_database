import os
import logging
from typing import List, Dict, Any
import mariadb
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BibleDatabase:
    """
    A client for connecting to the Bible Database in MariaDB.
    """

    def __init__(self, env_file: str = ".env"):
        """
        Initialize the Bible Database client.

        Args:
            env_file: Path to the .env file with connection details
        """
        # Load environment variables
        load_dotenv(env_file)

        # Set log level from environment or default to WARNING
        log_level = os.getenv("LOG_LEVEL", "WARNING")
        logger.setLevel(log_level)

        self.connection = None
        self.cursor = None

        # Database connection parameters
        self.db_config = {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "bible")
        }

        host = self.db_config['host']
        logger.info(f"Bible Database client initialized with host: {host}")

    def connect(self) -> None:
        """
        Connect to the MariaDB database.

        Raises:
            mariadb.Error: If connection to the database fails
        """
        try:
            self.connection = mariadb.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("Connected to the Bible database")
        except mariadb.Error as e:
            logger.error(f"Error connecting to the Bible database: {e}")
            raise

    def disconnect(self) -> None:
        """
        Close the database connection.
        """
        if self.cursor:
            self.cursor.close()
            self.cursor = None

        if self.connection:
            try:
                self.connection.close()
                logger.info("Disconnected from the Bible database")
            except Exception as e:
                logger.error(f"Error disconnecting from database: {e}")
            finally:
                self.connection = None

    def debug_sql(self, query, params=None):
        """
        Log a SQL query with parameters for debugging.

        Args:
            query: The SQL query string
            params: Query parameters (tuple, list, or None)
        """
        if params:
            debug_query = query
            for param in params:
                # Replace the first ? with the parameter value
                debug_query = debug_query.replace('?', repr(param), 1)
            logger.debug(f"SQL: {debug_query}")
        else:
            logger.debug(f"SQL: {query}")

    def ensure_connected(self) -> None:
        """
        Ensure that we have an active connection and cursor.

        This helper method checks if we have a valid database connection
        and cursor, establishing a connection if needed.

        Raises:
            RuntimeError: If connection attempt fails or cursor is not
                         available
        """
        if self.connection is None or self.cursor is None:
            self.connect()

        if self.cursor is None:
            raise RuntimeError("Database cursor could not be initialized.")

    def get_available_translations(self) -> List[Dict[str, str]]:
        """
        Get a list of available Bible translations in the database.

        Returns:
            List of dictionaries with translation information
        """
        try:
            # Get a typed cursor
            cursor = self.get_cursor()

            query = "SELECT * FROM bible_version_key"
            # Log the SQL query (requires DEBUG level logging)
            self.debug_sql(query)
            cursor.execute(query)
            return cursor.fetchall()
        except mariadb.Error as e:
            logger.error(f"Error fetching translations: {e}")
            return []

    def get_cursor(self):
        """
        Get the database cursor, ensuring connection is established.

        This method ensures we have a connection and returns a cursor
        that's properly typed for Pylance.

        Returns:
            A mariadb cursor object that's guaranteed to be not None
        """
        self.ensure_connected()
        # This assertion tells type checkers the cursor is not None
        assert self.cursor is not None
        return self.cursor

    def get_verses(
            self, ref: str, translation: str = "WEB") -> List[Dict[str, Any]]:
        """
        Get Bible verses from the database.

        Args:
            ref: Bible reference in the format "Book Chapter:Verse" or
                 "Book Chapter:Verse-EndVerse" or
                 "Book Chapter:Verse-EndChapter:EndVerse"
            translation: Bible translation code (e.g., "KJV", "ASV")

        Returns:
            List of dictionaries containing verse information

        Example:
            get_verses("Jude 13", translation="WEB")
            get_verses("John 3:16-17", translation="KJV")
        """
        # TODO: Implement this method to fetch verses from the database
        self.ensure_connected()
        if not ref:
            raise ValueError("Reference cannot be empty")

        # Parse the reference to get book, chapter, and verse
        try:
            start_ref, end_ref = self._parse_reference(ref)
        except ValueError as e:
            logger.error(f"Invalid reference format: {e}")
            raise

        # Get the table name based on the translation - i.e.
        # "SELECT `table` FROM bible.bible_version_key WHERE abbreviation = ?"
        translation = translation.upper()
        query = ("SELECT `table` FROM bible.bible_version_key "
                 "WHERE abbreviation = ?")
        try:
            cursor = self.get_cursor()
            cursor.execute(query, (translation,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(
                    f"Translation '{translation}' not found in database.")
            table_name = result['table']
        except mariadb.Error as e:
            logger.error(f"Error fetching translation table: {e}")
            raise

        # Ensure the table name is valid and contains only alphanumeric
        # characters
        if not table_name.isidentifier():
            raise ValueError(f"Invalid translation table name: {table_name}")

        # Build the SQL query to fetch the verses
        # The query will look like:
        # "SELECT * from ? WHERE id >= ? AND id <= ?"
        query = f"""
            SELECT c AS chapter, v AS verse, t AS text FROM {table_name}
            WHERE id >= ? AND id <= ?
        """
        params = (start_ref, end_ref)
        try:
            cursor.execute(query, params)
            # Log the SQL query (requires DEBUG level logging)
            self.debug_sql(query, params)
            results = cursor.fetchall()
            if not results:
                logger.warning(
                    f"No verses found for reference '{ref}' in translation "
                    f"'{translation}'"
                )
            return results
        except mariadb.Error as e:
            logger.error(f"Error fetching verses: {e}")
            raise

    def set_log_level(self, level: str = "INFO") -> None:
        """
        Set log level for the Bible Database client. Note that SQL logging is
        at the DEBUG level.

        Args:
            level: Log level as a string (e.g., "DEBUG", "INFO", "WARNING",
                   "ERROR", "CRITICAL")
        """
        # Validate the log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level '{level}'. Valid levels are: "
                f"{', '.join(valid_levels)}"
            )

        # Set the log level
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    def __enter__(self):
        """
        Context manager entry point. Used automatically by the start of a
        'with' statement. Establishes a connection to the database.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Used automatically at the end of a 'with'
        statement. Cleans up the connection.
        """
        self.disconnect()

    def _get_book_from_name(self, book_name: str):
        """
        Get the book number from the book name string, which may be one of the
        standard Bible book name abbreviations (e.g. 1 Ki, 2 Sam).
        """
        query = "SELECT b FROM key_abbreviations_english WHERE a = ?"
        try:
            cursor = self.get_cursor()
            cursor.execute(query, (book_name,))
            result = cursor.fetchone()
            if result:
                return result['b']
            else:
                raise ValueError(
                    f"Book name '{book_name}' not found in database.")
        except mariadb.Error as e:
            logger.error(f"Error fetching book from name '{book_name}': {e}")
            raise

    def _get_book_name_from_number(self, book_number: int):
        """
        Get the book name from the database's book number.
        """
        query = "SELECT n FROM key_english WHERE b = ?"
        try:
            cursor = self.get_cursor()
            cursor.execute(query, (book_number,))
            result = cursor.fetchone()
            if result:
                return result['n']
            else:
                raise ValueError(
                    f"Book number '{book_number}' not found in database.")
        except mariadb.Error as e:
            logger.error(
                f"Error fetching book from number '{book_number}': {e}")
            raise

    def _parse_reference(self, ref: str):
        """
        Parse a Bible reference like "John 3:16" or "Jude 13"
        """
        # The book is everything before the final space
        parts = ref.rsplit(" ", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid reference format: {ref}")
        book = parts[0].strip()
        chapter_verse = parts[1].strip()

        # Standardize the book name and get the book number
        book_number = self._get_book_from_name(book)
        # book_name = self._get_book_name_from_number(book_number)

        # The chapter_verse section could contain a range. E.g.:
        # "3:16-17" or "3:16-4:1". In the first example, the starting chapter
        # is 3 and the ending chapter is also 3. In the second example,
        # the starting chapter is 3 and the ending chapter is 4. The section
        # could also contain a range for a chapterless book like Jude, e.g.:
        # "1-13".

        # Split the chapter_verse into start and end
        if '-' in chapter_verse:
            # We have a range, e.g. "3:16-17" or "3:16-4:1"
            start, end = chapter_verse.split('-', 1)

            # If the start contains ":", it means we have a book with chapters
            # and verses, e.g. "John 3:16-17" or "John 3:16-4:1"
            if ':' in start:
                # Split start into chapter and verse
                start_chapter, start_verse = start.split(':', 1)
            else:
                # Chapterless book
                start_chapter = '1'
                start_verse = start.strip()
            if ':' in end:
                end_chapter, end_verse = end.split(':', 1)
            else:
                end_chapter = start_chapter
                end_verse = end.strip()
        else:
            # No range
            if ':' in chapter_verse:
                chapter, verse = chapter_verse.split(':', 1)
                start_chapter = chapter.strip()
                end_chapter = start_chapter
                start_verse = verse.strip()
                end_verse = start_verse
            else:
                start_chapter = '1'
                start_verse = chapter_verse.strip()
                end_chapter = start_chapter
                end_verse = start_verse

        # In the database, the references are held as:
        # - two digit book number, with leading zeroes
        # - three digit chapter number, with leading zeroes
        # - three digit verse number, with leading zeroes
        #
        # Return the book name, start and end references as a tuple
        return (f"{book_number:02d}{int(start_chapter):03d}"
                f"{int(start_verse):03d}",
                f"{book_number:02d}{int(end_chapter):03d}{int(end_verse):03d}")
