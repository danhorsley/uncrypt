import sqlite3
import logging
from contextlib import contextmanager
from .config import DATABASE_PATH


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
        
def update_db_schema():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if username column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]

        # Add username column if it doesn't exist
        if 'username' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT UNIQUE")
            conn.commit()
            logging.info("Added username column to users table")


def init_db():
    logging.info(f"Initializing SQLite database at {DATABASE_PATH}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS users (
              user_id TEXT PRIMARY KEY,
              email TEXT UNIQUE,
              username TEXT UNIQUE, 
              password_hash TEXT,
              auth_type TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              settings JSON
          )
      ''')

        # Create user_stats table
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS user_stats (
              user_id TEXT,
              current_streak INTEGER DEFAULT 0,
              max_streak INTEGER DEFAULT 0,
              total_games_played INTEGER DEFAULT 0,
              cumulative_score INTEGER DEFAULT 0,
              highest_monthly_score INTEGER DEFAULT 0,
              last_played_date TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users (id)
          )
      ''')

        # Create game_scores table
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS game_scores (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id TEXT,
              date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              time_taken INTEGER,
              mistakes INTEGER,
              score INTEGER,
              difficulty TEXT,
              is_clean_run BOOLEAN,
              FOREIGN KEY (user_id) REFERENCES users (id)
          )
      ''')

        conn.commit()
        logging.info("Database initialized successfully")

