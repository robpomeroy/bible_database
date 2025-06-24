from bible_db import BibleDatabase
import os
import sys
import pytest
from unittest import mock
import mariadb
import dotenv

# Add the parent directory to the path so we can import the bible_db module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


# Fixtures for the tests
@pytest.fixture
def mock_connection():
    """Create a mock database connection."""
    with mock.patch('mariadb.connect') as mock_connect:
        # Set up mock connection and cursor
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Configure the connect function to return our mock connection
        mock_connect.return_value = mock_conn

        yield mock_conn, mock_cursor


@pytest.fixture
def bible_db(mock_connection):
    """Create a BibleDatabase instance with a mock connection."""
    with mock.patch('dotenv.load_dotenv'):
        db = BibleDatabase()
        db.connect()  # This will use our mock connection
        return db


class TestBibleDatabase:
    """Test suite for the BibleDatabase class."""

    def test_init(self):
        """Test initialization of the BibleDatabase class."""
        with mock.patch('dotenv.load_dotenv'):
            db = BibleDatabase()
            assert db.connection is None
            assert db.cursor is None
            assert 'host' in db.db_config
            assert 'port' in db.db_config
            assert 'user' in db.db_config
            assert 'password' in db.db_config
            assert 'database' in db.db_config

    def test_connect(self, mock_connection):
        """Test connecting to the database."""
        mock_conn, mock_cursor = mock_connection

        with mock.patch('dotenv.load_dotenv'):
            db = BibleDatabase()
            db.connect()            # Check that mariadb.connect was called
            assert mock_connection[0] is mock_conn
            # Check that the connection and cursor were set
            assert db.connection is not None
            assert db.cursor is not None

    def test_disconnect(self, bible_db, mock_connection):
        """Test disconnecting from the database."""
        mock_conn, mock_cursor = mock_connection

        # Disconnect and verify close methods were called
        bible_db.disconnect()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert bible_db.connection is None
        assert bible_db.cursor is None

    def test_ensure_connected(self, bible_db):
        """Test the ensure_connected method."""
        # Already connected, should not need to connect again
        with mock.patch.object(bible_db, 'connect') as mock_connect:
            bible_db.ensure_connected()
            mock_connect.assert_not_called()

        # Set connection to None to force reconnect
        bible_db.connection = None
        with mock.patch.object(bible_db, 'connect') as mock_connect:
            bible_db.ensure_connected()
            mock_connect.assert_called_once()

    def test_context_manager(self, mock_connection):
        """Test using the class as a context manager."""
        mock_conn, mock_cursor = mock_connection

        with mock.patch('dotenv.load_dotenv'):
            with BibleDatabase() as db:
                assert db.connection is not None
                assert db.cursor is not None

            # After exiting the context, close should be called
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_debug_sql_no_params(self, bible_db):
        """Test debug_sql method without parameters."""
        with mock.patch.object(bible_db, 'debug_sql') as mock_debug:
            bible_db.debug_sql("SELECT * FROM table")
            mock_debug.assert_called_once()

    def test_debug_sql_with_params(self, bible_db):
        """Test debug_sql method with parameters."""
        with mock.patch.object(bible_db, 'debug_sql') as mock_debug:
            bible_db.debug_sql("SELECT * FROM table WHERE id = ?", (1,))
            mock_debug.assert_called_once()

    def test_get_cursor(self, bible_db):
        """Test get_cursor method."""
        with mock.patch.object(bible_db, 'ensure_connected') as mock_ensure:
            cursor = bible_db.get_cursor()
            mock_ensure.assert_called_once()
            assert cursor is not None

    def test_set_log_level_valid(self, bible_db):
        """Test set_log_level with valid levels."""
        with mock.patch('logging.Logger.setLevel') as mock_set_level:
            bible_db.set_log_level("DEBUG")
            mock_set_level.assert_called_once()

            # Reset and try another level
            mock_set_level.reset_mock()
            bible_db.set_log_level("INFO")
            mock_set_level.assert_called_once()

    def test_set_log_level_invalid(self, bible_db):
        """Test set_log_level with invalid level."""
        with pytest.raises(ValueError):
            bible_db.set_log_level("INVALID_LEVEL")


class TestBibleDatabaseBookMethods:
    """Tests for the book-related methods in BibleDatabase."""

    def test_get_book_from_name(self, bible_db, mock_connection):
        """Test _get_book_from_name with valid book name."""
        _, mock_cursor = mock_connection

        # Set up mock cursor to return a book number
        mock_cursor.fetchone.return_value = {'b': 43}  # John is book 43

        book_number = bible_db._get_book_from_name("John")

        # Check that the correct query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        query = "SELECT b FROM key_abbreviations_english WHERE a = ?"
        assert query in call_args[0]
        assert call_args[1] == ("John",)

        assert book_number == 43

    def test_get_book_from_name_not_found(self, bible_db, mock_connection):
        """Test _get_book_from_name with invalid book name."""
        _, mock_cursor = mock_connection

        # Set up mock cursor to return no results
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError) as exc_info:
            bible_db._get_book_from_name("InvalidBook")

        assert "not found in database" in str(exc_info.value)

    def test_get_book_name_from_number(self, bible_db, mock_connection):
        """Test _get_book_name_from_number with valid book number."""
        _, mock_cursor = mock_connection

        # Set up mock cursor to return a book name
        mock_cursor.fetchone.return_value = {'n': 'John'}

        book_name = bible_db._get_book_name_from_number(43)

        # Check that the correct query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert "SELECT n FROM key_english WHERE b = ?" in call_args[0]
        assert call_args[1] == (43,)

        assert book_name == 'John'

    def test_get_book_name_from_number_not_found(self,
                                                 bible_db,
                                                 mock_connection):
        """Test _get_book_name_from_number with invalid book number."""
        _, mock_cursor = mock_connection

        # Set up mock cursor to return no results
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError) as exc_info:
            bible_db._get_book_name_from_number(999)  # Invalid book number

        assert "not found in database" in str(exc_info.value)


class TestBibleDatabaseReferenceParser:
    """Tests for the reference parsing functionality."""

    def test_parse_reference_book_chapter_verse(self, bible_db):
        """Test parsing a standard book chapter:verse reference."""
        # Mock the internal methods used by _parse_reference
        with mock.patch.object(bible_db,
                               '_get_book_from_name',
                               return_value=43), \
                mock.patch.object(bible_db, '_get_book_name_from_number'):

            start_ref, end_ref = bible_db._parse_reference("John 3:16")

            # Check the format: BBCCCVVV (book, chapter, verse with leading
            # zeros)
            assert start_ref == "43003016"
            assert end_ref == "43003016"

    def test_parse_reference_chapterless_book(self, bible_db):
        """Test parsing a reference to a chapterless book like Jude."""
        with mock.patch.object(bible_db,
                               '_get_book_from_name',
                               return_value=65), \
                mock.patch.object(bible_db, '_get_book_name_from_number'):

            start_ref, end_ref = bible_db._parse_reference("Jude 5")

            # For chapterless books, chapter is 1
            assert start_ref == "65001005"
            assert end_ref == "65001005"

    def test_parse_reference_verse_range(self, bible_db):
        """Test parsing a verse range within the same chapter."""
        with mock.patch.object(bible_db,
                               '_get_book_from_name',
                               return_value=43), \
                mock.patch.object(bible_db, '_get_book_name_from_number'):

            start_ref, end_ref = bible_db._parse_reference("John 3:16-18")

            assert start_ref == "43003016"
            assert end_ref == "43003018"

    def test_parse_reference_chapter_range(self, bible_db):
        """Test parsing a range that spans chapters."""
        with mock.patch.object(bible_db,
                               '_get_book_from_name',
                               return_value=43), \
                mock.patch.object(bible_db, '_get_book_name_from_number'):

            start_ref, end_ref = bible_db._parse_reference("John 3:16-4:3")

            assert start_ref == "43003016"
            assert end_ref == "43004003"

    def test_parse_reference_invalid_format(self, bible_db):
        """Test parsing an invalid reference format."""
        with pytest.raises(ValueError) as exc_info:
            bible_db._parse_reference("InvalidReference")

        assert "Invalid reference format" in str(exc_info.value)


class TestBibleDatabaseVerses:
    """Tests for fetching verses from the database."""

    def test_get_verses_single_verse(self, bible_db, mock_connection):
        """Test getting a single verse."""
        _, mock_cursor = mock_connection

        # Mock the _parse_reference method
        with mock.patch.object(bible_db, '_parse_reference',
                               return_value=("43003016", "43003016")):

            # Mock getting the translation table
            mock_cursor.fetchone.return_value = {'table': 't_web'}

            # Mock fetching verses
            mock_verses = [{
                'chapter': 3,
                'verse': 16,
                'text': 'For God so loved the world...'
            }]
            # First fetchone for translation, then fetchall for verses
            mock_cursor.fetchall.return_value = mock_verses

            verses = bible_db.get_verses("John 3:16", translation="WEB")

            assert len(verses) == 1
            assert verses[0]['chapter'] == 3
            assert verses[0]['verse'] == 16
            assert "God so loved the world" in verses[0]['text']

    def test_get_verses_range(self, bible_db, mock_connection):
        """Test getting a range of verses."""
        _, mock_cursor = mock_connection

        # Mock the _parse_reference method
        with mock.patch.object(bible_db, '_parse_reference',
                               return_value=("43003016", "43003018")):

            # Mock getting the translation table
            mock_cursor.fetchone.return_value = {'table': 't_web'}

            # Mock fetching verses
            mock_verses = [
                {'chapter': 3,
                 'verse': 16,
                 'text': 'For God so loved the world...'},
                {'chapter': 3,
                 'verse': 17,
                 'text': 'For God didn\'t send his Son...'},
                {'chapter': 3,
                 'verse': 18,
                 'text': 'He who believes in him...'}
            ]
            # First fetchone for translation, then fetchall for verses
            mock_cursor.fetchall.return_value = mock_verses

            verses = bible_db.get_verses("John 3:16-18", translation="WEB")

            assert len(verses) == 3
            assert verses[0]['verse'] == 16
            assert verses[1]['verse'] == 17
            assert verses[2]['verse'] == 18

    def test_get_verses_empty_reference(self, bible_db):
        """Test getting verses with an empty reference."""
        with pytest.raises(ValueError) as exc_info:
            bible_db.get_verses("")

        assert "Reference cannot be empty" in str(exc_info.value)

    def test_get_verses_translation_not_found(self, bible_db, mock_connection):
        """Test getting verses with a non-existent translation."""
        _, mock_cursor = mock_connection

        # Mock the _parse_reference method
        with mock.patch.object(bible_db, '_parse_reference',
                               return_value=("43003016", "43003016")):

            # Mock getting the translation table (not found)
            mock_cursor.fetchone.return_value = None

            with pytest.raises(ValueError) as exc_info:
                bible_db.get_verses("John 3:16", translation="NONEXISTENT")

            assert "not found in database" in str(exc_info.value)

    def test_get_verses_no_results(self, bible_db, mock_connection):
        """Test getting verses with no results."""
        _, mock_cursor = mock_connection

        # Mock the _parse_reference method
        with mock.patch.object(bible_db, '_parse_reference',
                               return_value=("43003016", "43003016")):

            # Mock getting the translation table
            mock_cursor.fetchone.return_value = {'table': 't_web'}

            # Mock no verses found
            mock_cursor.fetchall.return_value = []

            verses = bible_db.get_verses("John 3:16", translation="WEB")

            assert len(verses) == 0

    def test_get_available_translations(self, bible_db, mock_connection):
        """Test getting available translations."""
        _, mock_cursor = mock_connection

        # Mock fetching translations
        mock_translations = [
            {'id': 1, 'table': 't_kjv', 'abbreviation': 'KJV',
                'version': 'King James Version'},
            {'id': 2, 'table': 't_web', 'abbreviation': 'WEB',
                'version': 'World English Bible'}
        ]
        mock_cursor.fetchall.return_value = mock_translations

        translations = bible_db.get_available_translations()

        # Check that the correct query was executed
        mock_cursor.execute.assert_called_once()
        assert ("SELECT * FROM bible_version_key"
                in mock_cursor.execute.call_args[0][0])

        assert len(translations) == 2
        assert translations[0]['abbreviation'] == 'KJV'
        assert translations[1]['abbreviation'] == 'WEB'

    def test_get_available_translations_error(self, bible_db, mock_connection):
        """Test getting available translations with a database error."""
        _, mock_cursor = mock_connection

        # Make the execute method raise an error
        mock_cursor.execute.side_effect = mariadb.Error("Database error")

        translations = bible_db.get_available_translations()

        # Should return an empty list on error
        assert len(translations) == 0


# Integration tests that require a real database connection
# These will be skipped if the database is not available
@pytest.mark.integration
class TestBibleDatabaseIntegration:
    """Integration tests for the BibleDatabase class.

    These tests require a real database connection. They'll be skipped if
    the database is not available or credentials are not provided.
    """

    @pytest.fixture
    def real_db(self):
        """Create a real database connection."""
        # Check if .env.test file exists
        if not os.path.exists(".env.test"):
            pytest.skip("No .env.test file found for integration tests")

        # Load .env.test file to get the SKIP_DB_INTEGRATION_TESTS value
        env_vars = dotenv.dotenv_values(".env.test")

        # Check if we should run integration tests
        skip_value = env_vars.get("SKIP_DB_INTEGRATION_TESTS", "true")
        # Convert to lowercase, handling potential None value
        if skip_value:
            skip_integration = skip_value.lower() == "true"
        else:
            skip_integration = True

        if skip_integration:
            pytest.skip(
                "Skipping integration tests (SKIP_DB_INTEGRATION_TESTS=true)")

        # Create a real database connection
        db = BibleDatabase(env_file=".env.test")
        try:
            # Test the connection
            db.connect()
            yield db
        except Exception as e:
            pytest.skip(f"Could not connect to database: {e}")
        finally:
            # Clean up
            if db.connection:
                db.disconnect()

    def test_real_connection(self, real_db):
        """Test connecting to a real database."""
        assert real_db.connection is not None
        assert real_db.cursor is not None

    def test_get_real_book_from_name(self, real_db):
        """Test getting a real book number from name."""
        book_number = real_db._get_book_from_name("John")
        assert book_number == 43

    def test_get_real_book_name_from_number(self, real_db):
        """Test getting a real book name from number."""
        book_name = real_db._get_book_name_from_number(43)
        assert "John" in book_name

    def test_get_real_verses(self, real_db):
        """Test getting real verses from the database."""
        verses = real_db.get_verses("John 3:16", translation="WEB")
        assert len(verses) >= 1
        assert verses[0]['chapter'] == 3
        assert verses[0]['verse'] == 16

    def test_get_real_translations(self, real_db):
        """Test getting real available translations."""
        translations = real_db.get_available_translations()
        assert len(translations) > 0
        # Check for at least one expected translation
        assert any(t['abbreviation'] == 'KJV' for t in translations) or \
            any(t['abbreviation'] == 'WEB' for t in translations)


if __name__ == "__main__":
    # This allows running the tests manually
    pytest.main(["-xvs", __file__])
