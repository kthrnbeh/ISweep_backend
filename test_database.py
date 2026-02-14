import pytest
from database import Database

class TestDatabase:
    """Test database operations."""
    
    def test_create_user(self, database):
        """Test creating a new user."""
        user_id = database.create_user('testuser')
        assert user_id is not None
        assert user_id > 0
    
    def test_create_duplicate_user(self, database):
        """Test that duplicate username returns None."""
        database.create_user('testuser')
        user_id = database.create_user('testuser')
        assert user_id is None
    
    def test_get_user_by_id(self, database):
        """Test retrieving user by ID."""
        user_id = database.create_user('testuser')
        user = database.get_user_by_id(user_id)
        assert user is not None
        assert user['username'] == 'testuser'
    
    def test_get_user_by_username(self, database):
        """Test retrieving user by username."""
        database.create_user('testuser')
        user = database.get_user_by_username('testuser')
        assert user is not None
        assert user['username'] == 'testuser'
    
    def test_get_nonexistent_user(self, database):
        """Test that getting non-existent user returns None."""
        user = database.get_user_by_id(9999)
        assert user is None
    
    def test_default_preferences(self, database):
        """Test that new users have default preferences."""
        user_id = database.create_user('testuser')
        prefs = database.get_user_preferences(user_id)
        
        assert prefs is not None
        assert prefs['language_filter'] == 1  # True
        assert prefs['sexual_content_filter'] == 1
        assert prefs['violence_filter'] == 1
        assert prefs['language_sensitivity'] == 'medium'
        assert prefs['sexual_content_sensitivity'] == 'medium'
        assert prefs['violence_sensitivity'] == 'medium'
    
    def test_update_preferences(self, database):
        """Test updating user preferences."""
        user_id = database.create_user('testuser')
        
        # Update preferences
        success = database.update_user_preferences(user_id, {
            'language_filter': False,
            'violence_sensitivity': 'high'
        })
        assert success is True
        
        # Verify update
        prefs = database.get_user_preferences(user_id)
        assert prefs['language_filter'] == 0  # False
        assert prefs['violence_sensitivity'] == 'high'
    
    def test_update_all_preferences(self, database):
        """Test updating all preference fields."""
        user_id = database.create_user('testuser')
        
        new_prefs = {
            'language_filter': False,
            'sexual_content_filter': False,
            'violence_filter': True,
            'language_sensitivity': 'low',
            'sexual_content_sensitivity': 'high',
            'violence_sensitivity': 'medium'
        }
        
        success = database.update_user_preferences(user_id, new_prefs)
        assert success is True
        
        # Verify all updates
        prefs = database.get_user_preferences(user_id)
        assert prefs['language_filter'] == 0
        assert prefs['sexual_content_filter'] == 0
        assert prefs['violence_filter'] == 1
        assert prefs['language_sensitivity'] == 'low'
        assert prefs['sexual_content_sensitivity'] == 'high'
        assert prefs['violence_sensitivity'] == 'medium'
