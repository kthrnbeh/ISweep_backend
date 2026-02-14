import sqlite3
import json
from typing import Dict, Optional

class Database:
    """Simple SQLite database handler for user preferences."""
    
    def __init__(self, db_path: str = 'isweep.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table with preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user_preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                language_filter BOOLEAN DEFAULT 1,
                sexual_content_filter BOOLEAN DEFAULT 1,
                violence_filter BOOLEAN DEFAULT 1,
                language_sensitivity TEXT DEFAULT 'medium',
                sexual_content_sensitivity TEXT DEFAULT 'medium',
                violence_sensitivity TEXT DEFAULT 'medium',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str) -> Optional[int]:
        """Create a new user with default preferences."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create user
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            user_id = cursor.lastrowid
            
            # Create default preferences
            cursor.execute('''
                INSERT INTO user_preferences (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        """Get user preferences."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        prefs = cursor.fetchone()
        conn.close()
        
        if prefs:
            return dict(prefs)
        return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Update user preferences."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically based on provided preferences
        allowed_fields = [
            'language_filter', 'sexual_content_filter', 'violence_filter',
            'language_sensitivity', 'sexual_content_sensitivity', 'violence_sensitivity'
        ]
        
        updates = []
        values = []
        for field in allowed_fields:
            if field in preferences:
                updates.append(f'{field} = ?')
                values.append(preferences[field])
        
        if not updates:
            conn.close()
            return False
        
        values.append(user_id)
        query = f'UPDATE user_preferences SET {", ".join(updates)} WHERE user_id = ?'
        
        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success
