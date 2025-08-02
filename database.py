import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: str = "db/project_planner.db"):
        self.db_path = db_path
        # Ensure the db directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL CHECK(length(name) <= 64),
                    display_name TEXT NOT NULL CHECK(length(display_name) <= 64),
                    creation_time TEXT NOT NULL
                )
            ''')
            
            # Create teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL CHECK(length(name) <= 64),
                    description TEXT CHECK(length(description) <= 128),
                    admin_id INTEGER NOT NULL,
                    creation_time TEXT NOT NULL,
                    FOREIGN KEY (admin_id) REFERENCES users (id)
                )
            ''')
            
            # Create team_members table (many-to-many relationship)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (team_id) REFERENCES teams (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(team_id, user_id)
                )
            ''')
            
            # Create boards table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL CHECK(length(name) <= 64),
                    description TEXT CHECK(length(description) <= 128),
                    team_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED')),
                    creation_time TEXT NOT NULL,
                    end_time TEXT,
                    FOREIGN KEY (team_id) REFERENCES teams (id),
                    UNIQUE(name, team_id)
                )
            ''')
            
            # Create tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL CHECK(length(title) <= 64),
                    description TEXT CHECK(length(description) <= 128),
                    board_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'IN_PROGRESS', 'COMPLETE')),
                    creation_time TEXT NOT NULL,
                    FOREIGN KEY (board_id) REFERENCES boards (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(title, board_id)
                )
            ''')
            
            conn.commit()


# Global database instance
db = Database()


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def validate_json_input(data: str) -> Dict[Any, Any]:
    """Validate and parse JSON input"""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON format")


def format_json_response(data: Any) -> str:
    """Format response as JSON string"""
    return json.dumps(data, indent=2) 