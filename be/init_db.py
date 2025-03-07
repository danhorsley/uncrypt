import sqlite3
import logging
import os
from contextlib import contextmanager

# Database path - using different files for dev and prod
ENV = os.environ.get('FLASK_ENV', 'development')
if ENV == 'production':
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.db')  # Production database
else:
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev_game.db')  # Development database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

@contextmanager
def get_db_connection():
    """Create a database connection with Row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with all required tables"""
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
                settings TEXT
            )
        ''')

        # Create game_scores table with all necessary fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_id TEXT,
                date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_taken INTEGER,
                mistakes INTEGER,
                score INTEGER,
                difficulty TEXT,
                is_clean_run BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Create user_stats table for tracking performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                total_games_played INTEGER DEFAULT 0,
                cumulative_score INTEGER DEFAULT 0,
                highest_score INTEGER DEFAULT 0,
                last_played_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Create a leaderboard table (if needed for performance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                score INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                date_achieved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Create saved_quotes table for curating quotes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL,
                major_attribution TEXT,
                minor_attribution TEXT,
                saved_by TEXT,
                date_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (saved_by) REFERENCES users (user_id)
            )
        ''')

        conn.commit()
        logging.info("Database tables created successfully")

def update_db_schema():
    """Update existing database schema if needed"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if username column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]

        # Add username column if it doesn't exist
        if 'username' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT UNIQUE")
            conn.commit()
            logging.info("Added username column to users table")

        # Check if game_scores table has the time_taken column
        cursor.execute("PRAGMA table_info(game_scores)")
        game_score_columns = [info[1] for info in cursor.fetchall()]

        if 'time_taken' not in game_score_columns and len(game_score_columns) > 0:
            logging.info("Updating game_scores table schema...")
            # SQLite doesn't support ADD COLUMN with non-null constraints
            # We'll need to recreate the table for a proper schema update

            # Backup existing data
            cursor.execute("ALTER TABLE game_scores RENAME TO game_scores_old")

            # Create new table with proper schema
            cursor.execute('''
                CREATE TABLE game_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    game_id TEXT,
                    date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    time_taken INTEGER,
                    mistakes INTEGER,
                    score INTEGER,
                    difficulty TEXT,
                    is_clean_run BOOLEAN,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Transfer data from old table to new table
            # Get columns from old table
            cursor.execute("PRAGMA table_info(game_scores_old)")
            old_columns = [info[1] for info in cursor.fetchall()]

            # Build the migration query with columns that exist in both tables
            common_columns = [col for col in old_columns if col in 
                              ['id', 'user_id', 'game_id', 'date_played', 
                               'mistakes', 'score', 'difficulty', 'is_clean_run']]

            if common_columns:
                columns_str = ', '.join(common_columns)
                cursor.execute(f'''
                    INSERT INTO game_scores ({columns_str})
                    SELECT {columns_str} FROM game_scores_old
                ''')

            # Drop the old table
            cursor.execute("DROP TABLE game_scores_old")
            conn.commit()
            logging.info("Updated game_scores table schema")

        conn.commit()
        logging.info("Database schema updated successfully")

if __name__ == "__main__":
    # If run directly, initialize the database
    init_db()
    update_db_schema()
    logging.info("Database initialization complete")