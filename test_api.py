import pytest
import json

class TestAPI:
    """Test the REST API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'ISweep Backend'
    
    def test_create_user(self, client):
        """Test creating a new user."""
        response = client.post('/api/users', 
                              json={'username': 'testuser'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['username'] == 'testuser'
        assert 'user_id' in data
        assert 'preferences' in data
    
    def test_create_duplicate_user(self, client):
        """Test that duplicate username is rejected."""
        client.post('/api/users', json={'username': 'testuser'})
        response = client.post('/api/users', json={'username': 'testuser'})
        assert response.status_code == 409
    
    def test_create_user_without_username(self, client):
        """Test that creating user without username fails."""
        response = client.post('/api/users', json={})
        assert response.status_code == 400
    
    def test_get_preferences(self, client):
        """Test getting user preferences."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Get preferences
        response = client.get(f'/api/users/{user_id}/preferences')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['language_filter'] == 1  # SQLite stores boolean as int
        assert data['sexual_content_filter'] == 1
        assert data['violence_filter'] == 1
    
    def test_get_preferences_nonexistent_user(self, client):
        """Test getting preferences for non-existent user."""
        response = client.get('/api/users/9999/preferences')
        assert response.status_code == 404
    
    def test_update_preferences(self, client):
        """Test updating user preferences."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Update preferences
        update_data = {
            'language_filter': False,
            'violence_sensitivity': 'high'
        }
        response = client.put(f'/api/users/{user_id}/preferences', json=update_data)
        assert response.status_code == 200
        
        # Verify update
        data = json.loads(response.data)
        assert data['preferences']['language_filter'] == 0  # False as int
        assert data['preferences']['violence_sensitivity'] == 'high'
    
    def test_update_preferences_invalid_sensitivity(self, client):
        """Test that invalid sensitivity values are rejected."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Try to update with invalid sensitivity
        update_data = {
            'language_sensitivity': 'invalid'
        }
        response = client.put(f'/api/users/{user_id}/preferences', json=update_data)
        assert response.status_code == 400
    
    def test_analyze_clean_content(self, client):
        """Test analyzing clean content."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Analyze clean content
        response = client.post('/api/analyze', json={
            'user_id': user_id,
            'text': 'This is a beautiful day with wonderful weather'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'none'
        assert data['user_id'] == user_id
    
    def test_analyze_profanity(self, client):
        """Test analyzing content with profanity."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Analyze profanity
        response = client.post('/api/analyze', json={
            'user_id': user_id,
            'text': 'This is damn stupid'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'mute'
    
    def test_analyze_violence(self, client):
        """Test analyzing violent content."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Analyze violence
        response = client.post('/api/analyze', json={
            'user_id': user_id,
            'text': 'He was shot and killed in the fight'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'fast_forward'
    
    def test_analyze_sexual_content(self, client):
        """Test analyzing sexual content."""
        # Create a user first
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Analyze sexual content
        response = client.post('/api/analyze', json={
            'user_id': user_id,
            'text': 'The sexual scene was explicit'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'skip'
    
    def test_analyze_missing_fields(self, client):
        """Test that analyze endpoint requires user_id and text."""
        response = client.post('/api/analyze', json={'text': 'some text'})
        assert response.status_code == 400
        
        response = client.post('/api/analyze', json={'user_id': 1})
        assert response.status_code == 400
    
    def test_analyze_nonexistent_user(self, client):
        """Test analyzing with non-existent user."""
        response = client.post('/api/analyze', json={
            'user_id': 9999,
            'text': 'some text'
        })
        assert response.status_code == 404
    
    def test_analyze_with_disabled_filters(self, client):
        """Test that disabled filters don't trigger actions."""
        # Create a user
        create_response = client.post('/api/users', json={'username': 'testuser'})
        user_id = json.loads(create_response.data)['user_id']
        
        # Disable all filters
        client.put(f'/api/users/{user_id}/preferences', json={
            'language_filter': False,
            'sexual_content_filter': False,
            'violence_filter': False
        })
        
        # Analyze content that would normally trigger actions
        response = client.post('/api/analyze', json={
            'user_id': user_id,
            'text': 'This damn violent sexual content'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'none'

    def test_event_schema_and_priority(self, client):
        """Test /event returns expected schema and prioritizes sexual over others."""
        create_response = client.post('/api/users', json={'username': 'eventuser'})
        user_id = json.loads(create_response.data)['user_id']

        response = client.post('/event', json={
            'user_id': str(user_id),
            'text': 'Explicit sexual content and sexual scene with a violent fight and strong language'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert set(data.keys()) == {'action', 'duration_seconds', 'matched_category', 'reason'}
        assert data['action'] == 'skip'
        assert data['matched_category'] == 'sexual'
        assert isinstance(data['duration_seconds'], int) and data['duration_seconds'] > 0
        assert isinstance(data['reason'], str) and data['reason']

    def test_event_no_match(self, client):
        """Test /event returns none when no categories match."""
        create_response = client.post('/api/users', json={'username': 'eventnomatch'})
        user_id = json.loads(create_response.data)['user_id']

        response = client.post('/event', json={
            'user_id': user_id,
            'text': 'Lovely sunny afternoon with friends'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'none'
        assert data['duration_seconds'] == 0
        assert data['matched_category'] is None
        assert data['reason'] == 'No match'

    def test_event_invalid_request(self, client):
        """Test /event returns schema for invalid payload."""
        response = client.post('/event', json={'text': 'missing user id'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'none'
        assert data['duration_seconds'] == 0
        assert data['matched_category'] is None
        assert data['reason'] == 'Invalid request'

    def test_event_unknown_user(self, client):
        """Test /event returns schema when user is unknown."""
        response = client.post('/event', json={'user_id': 'nope', 'text': 'anything'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['action'] == 'none'
        assert data['duration_seconds'] == 0
        assert data['matched_category'] is None
        assert data['reason'] == 'Unknown user_id'
