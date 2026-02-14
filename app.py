from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

from database import Database
from content_analyzer import ContentAnalyzer

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
CORS(app)  # Enable CORS for browser, mobile, and TV platforms

# Initialize database and content analyzer
# These will be created once and reused for the lifetime of the app
def get_db():
    """Get database instance."""
    if not hasattr(app, 'database'):
        db_path = os.getenv('DATABASE_PATH', 'isweep.db')
        app.database = Database(db_path)
    return app.database

def get_analyzer():
    """Get content analyzer instance."""
    if not hasattr(app, 'analyzer'):
        app.analyzer = ContentAnalyzer()
    return app.analyzer


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for client resilience.
    Clients can check if backend is available and remain functional if not.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'ISweep Backend',
        'version': '1.0.0'
    }), 200


@app.route('/api/users', methods=['POST'])
def create_user():
    """
    Create a new user with default filtering preferences.
    
    Request body:
        {
            "username": "user123"
        }
    
    Response:
        {
            "user_id": 1,
            "username": "user123",
            "preferences": {...}
        }
    """
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'Username is required'}), 400
    
    username = data['username']
    db = get_db()
    user_id = db.create_user(username)
    
    if user_id is None:
        return jsonify({'error': 'Username already exists'}), 409
    
    preferences = db.get_user_preferences(user_id)
    
    return jsonify({
        'user_id': user_id,
        'username': username,
        'preferences': preferences
    }), 201


@app.route('/api/users/<int:user_id>/preferences', methods=['GET'])
def get_preferences(user_id):
    """
    Get user filtering preferences.
    
    Response:
        {
            "user_id": 1,
            "language_filter": true,
            "sexual_content_filter": true,
            "violence_filter": true,
            "language_sensitivity": "medium",
            "sexual_content_sensitivity": "medium",
            "violence_sensitivity": "medium"
        }
    """
    db = get_db()
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    preferences = db.get_user_preferences(user_id)
    return jsonify(preferences), 200


@app.route('/api/users/<int:user_id>/preferences', methods=['PUT'])
def update_preferences(user_id):
    """
    Update user filtering preferences.
    
    Request body:
        {
            "language_filter": true,
            "sexual_content_filter": false,
            "violence_filter": true,
            "language_sensitivity": "high",
            "sexual_content_sensitivity": "low",
            "violence_sensitivity": "medium"
        }
    
    Response:
        {
            "message": "Preferences updated successfully",
            "preferences": {...}
        }
    """
    db = get_db()
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Validate sensitivity values
    valid_sensitivities = ['low', 'medium', 'high']
    for field in ['language_sensitivity', 'sexual_content_sensitivity', 'violence_sensitivity']:
        if field in data and data[field] not in valid_sensitivities:
            return jsonify({'error': f'Invalid {field}. Must be one of: {", ".join(valid_sensitivities)}'}), 400
    
    success = db.update_user_preferences(user_id, data)
    
    if not success:
        return jsonify({'error': 'Failed to update preferences'}), 500
    
    preferences = db.get_user_preferences(user_id)
    return jsonify({
        'message': 'Preferences updated successfully',
        'preferences': preferences
    }), 200


@app.route('/api/analyze', methods=['POST'])
def analyze_content():
    """
    Real-time decision engine: analyze caption/transcript text and return playback action.
    
    Request body:
        {
            "user_id": 1,
            "text": "This is the caption or transcript text to analyze"
        }
    
    Response:
        {
            "action": "mute" | "skip" | "fast_forward" | "none",
            "text": "original text",
            "user_id": 1
        }
    
    Actions:
        - mute: Temporarily mute audio (for language/profanity)
        - skip: Skip ahead (for sexual content scenes)
        - fast_forward: Fast forward (for violence scenes)
        - none: No action needed, content is acceptable
    """
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'text' not in data:
        return jsonify({'error': 'user_id and text are required'}), 400
    
    user_id = data['user_id']
    text = data['text']
    
    db = get_db()
    # Verify user exists
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user preferences
    preferences = db.get_user_preferences(user_id)
    
    # Analyze content and determine action
    analyzer = get_analyzer()
    action = analyzer.analyze(text, preferences)
    
    return jsonify({
        'action': action,
        'text': text,
        'user_id': user_id
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
