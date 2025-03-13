# game_state.py - Enhanced with middleware functionality for game state persistence
from flask import session
import json
import logging
import datetime
from .init_db import get_db_connection


# Maximum age of active game states before automatic cleanup (in hours)
MAX_GAME_STATE_AGE_HOURS = 48

# Global game states dictionary (in-memory cache)
game_states_cache = {}


def save_game_state(user_id, game_id, game_state):
    """
    Save or update an active game state for a user

    Args:
        user_id (str): The user's ID
        game_id (str): The game's unique ID
        game_state (dict): The game state to save

    Returns:
        bool: True if successful, False otherwise
    """
    if not user_id or not game_id or not game_state:
        logging.warning(
            f"Missing required parameters for save_game_state: user_id={user_id}, game_id={game_id}"
        )
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # First delete any existing game state for this user
            # (ensures only one active game per user)
            cursor.execute('DELETE FROM active_game_states WHERE user_id = ?',
                           (user_id, ))

            # Prepare data for insertion
            correctly_guessed_json = json.dumps(
                game_state.get('correctly_guessed', []))
            mapping_json = json.dumps(game_state.get('mapping', {}))

            # Format reverse_mapping if needed
            reverse_mapping = game_state.get('reverse_mapping', {})
            if not reverse_mapping and 'mapping' in game_state:
                # Generate reverse mapping if not provided
                reverse_mapping = {
                    v: k
                    for k, v in game_state['mapping'].items()
                }
            reverse_mapping_json = json.dumps(reverse_mapping)

            # Insert the new game state
            cursor.execute(
                '''
                INSERT INTO active_game_states (
                    user_id, game_id, original_paragraph, encrypted_paragraph,
                    mapping, reverse_mapping, correctly_guessed, mistakes,
                    major_attribution, minor_attribution
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, game_id, game_state.get('original_paragraph', ''),
                  game_state.get('encrypted_paragraph',
                                 ''), mapping_json, reverse_mapping_json,
                  correctly_guessed_json, game_state.get(
                      'mistakes', 0), game_state.get('major_attribution', ''),
                  game_state.get('minor_attribution', '')))

            conn.commit()
            logging.info(
                f"Game state saved for user {user_id}, game {game_id}")

            # Update in-memory cache
            game_states_cache[game_id] = game_state

            return True

    except Exception as e:
        logging.error(f"Error saving game state: {e}")
        return False


def get_active_game_state(user_id):
    """
    Retrieve the active game state for a user

    Args:
        user_id (str): The user's ID

    Returns:
        dict: The game state if found, None otherwise
    """
    if not user_id:
        return None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                SELECT * FROM active_game_states
                WHERE user_id = ?
            ''', (user_id, ))

            row = cursor.fetchone()
            if not row:
                return None

            # Convert row to dictionary
            game_state = dict(row)

            # Parse JSON fields
            try:
                game_state['mapping'] = json.loads(game_state['mapping'])
                game_state['correctly_guessed'] = json.loads(
                    game_state['correctly_guessed'])

                # Parse reverse_mapping if exists in DB
                if 'reverse_mapping' in game_state and game_state[
                        'reverse_mapping']:
                    game_state['reverse_mapping'] = json.loads(
                        game_state['reverse_mapping'])
                else:
                    # Generate it if not available
                    game_state['reverse_mapping'] = {
                        v: k
                        for k, v in game_state['mapping'].items()
                    }

            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error parsing game state JSON: {e}")
                # Set defaults if parsing fails
                game_state['mapping'] = {}
                game_state['correctly_guessed'] = []
                game_state['reverse_mapping'] = {}

            # Create a properly structured game state dictionary for the frontend
            formatted_state = {
                'game_id': game_state['game_id'],
                'original_paragraph': game_state['original_paragraph'],
                'encrypted_paragraph': game_state['encrypted_paragraph'],
                'mapping': game_state['mapping'],
                'reverse_mapping': game_state['reverse_mapping'],
                'correctly_guessed': game_state['correctly_guessed'],
                'mistakes': game_state['mistakes'],
                'major_attribution': game_state['major_attribution'],
                'minor_attribution': game_state['minor_attribution'],
                'is_restored': True  # Flag indicating this is a restored state
            }

            # Update in-memory cache
            game_states_cache[game_state['game_id']] = formatted_state

            return formatted_state

    except Exception as e:
        logging.error(f"Error retrieving game state: {e}")
        return None


def sync_game_state_with_session(game_id=None, user_id=None):
    """
    Synchronize the database game state with the session game state
    Used after operations like guess and hint to keep them in sync

    Args:
        game_id (str, optional): The game's unique ID
        user_id (str, optional): The user's ID

    Returns:
        bool: True if sync was successful, False otherwise
    """
    # Get the game_id from session if not provided
    if not game_id:
        game_state = session.get('game_state')
        if game_state:
            game_id = game_state.get('game_id')

    # Get the user_id from session if not provided
    if not user_id:
        user_id = session.get('user_id')

    # Both game_id and user_id are required
    if not game_id or not user_id:
        logging.warning(
            f"Missing required parameters for sync: game_id={game_id}, user_id={user_id}"
        )
        return False

    try:
        # Get current state from session
        session_state = session.get('game_state')
        if not session_state:
            logging.warning("No game state in session to sync")
            return False

        # Make sure game_id is in the session state
        session_state['game_id'] = game_id

        # Update the database with session state
        return save_game_state(user_id, game_id, session_state)

    except Exception as e:
        logging.error(f"Error syncing game state: {e}")
        return False


def load_game_state_to_session(user_id):
    """
    Load a user's active game state into the session

    Args:
        user_id (str): The user's ID

    Returns:
        bool: True if a game was loaded, False otherwise
    """
    if not user_id:
        return False

    # Get the active game state from the database
    game_state = get_active_game_state(user_id)

    if not game_state:
        logging.info(f"No active game found for user {user_id}")
        return False

    # Store the game state in the session
    session['game_state'] = game_state

    # Also update the in-memory cache
    game_states_cache[game_state['game_id']] = game_state

    logging.info(
        f"Loaded active game {game_state['game_id']} for user {user_id}")
    return True


def delete_game_state(user_id=None, game_id=None):
    """
    Delete an active game state by user ID or game ID
    At least one parameter must be provided

    Args:
        user_id (str, optional): The user's ID
        game_id (str, optional): The game's unique ID

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not user_id and not game_id:
        logging.error(
            "Either user_id or game_id must be provided to delete_game_state")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if user_id:
                # Get game_id first for cache cleanup
                if not game_id:
                    cursor.execute(
                        'SELECT game_id FROM active_game_states WHERE user_id = ?',
                        (user_id, ))
                    result = cursor.fetchone()
                    if result:
                        game_id = result['game_id']

                cursor.execute(
                    'DELETE FROM active_game_states WHERE user_id = ?',
                    (user_id, ))
                logging.info(f"Deleted game state for user {user_id}")
            else:
                cursor.execute(
                    'DELETE FROM active_game_states WHERE game_id = ?',
                    (game_id, ))
                logging.info(f"Deleted game state for game {game_id}")

            conn.commit()

            # Also clean up the in-memory cache
            if game_id and game_id in game_states_cache:
                del game_states_cache[game_id]

            return cursor.rowcount > 0

    except Exception as e:
        logging.error(f"Error deleting game state: {e}")
        return False


def cleanup_old_game_states(max_age_hours=MAX_GAME_STATE_AGE_HOURS):
    """
    Delete game states that are older than the specified age

    Args:
        max_age_hours (int): Maximum age in hours

    Returns:
        int: Number of deleted game states
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Calculate cutoff timestamp
            cutoff_time = datetime.datetime.now() - datetime.timedelta(
                hours=max_age_hours)

            # Get game_ids to remove from cache
            cursor.execute(
                'SELECT game_id FROM active_game_states WHERE created_at < ?',
                (cutoff_time.isoformat(), ))
            old_games = cursor.fetchall()

            # Delete old game states
            cursor.execute(
                'DELETE FROM active_game_states WHERE created_at < ?',
                (cutoff_time.isoformat(), ))

            deleted_count = cursor.rowcount
            conn.commit()

            # Also clean up the in-memory cache
            for game in old_games:
                game_id = game['game_id']
                if game_id in game_states_cache:
                    del game_states_cache[game_id]

            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} old game states")

            return deleted_count

    except Exception as e:
        logging.error(f"Error cleaning up old game states: {e}")
        return 0


# This function should be called on application startup
def init_game_state_cache():
    """
    Initialize the in-memory game state cache from the database
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get all active game states
            cursor.execute('SELECT * FROM active_game_states')
            rows = cursor.fetchall()

            loaded_count = 0
            for row in cursor.fetchall():
                try:
                    game_state = dict(row)

                    # Parse JSON fields
                    game_state['mapping'] = json.loads(game_state['mapping'])
                    game_state['correctly_guessed'] = json.loads(
                        game_state['correctly_guessed'])

                    # Parse reverse_mapping if exists
                    if 'reverse_mapping' in game_state and game_state[
                            'reverse_mapping']:
                        game_state['reverse_mapping'] = json.loads(
                            game_state['reverse_mapping'])
                    else:
                        # Generate it if not available
                        game_state['reverse_mapping'] = {
                            v: k
                            for k, v in game_state['mapping'].items()
                        }

                    # Add to cache
                    game_states_cache[game_state['game_id']] = {
                        'game_id': game_state['game_id'],
                        'original_paragraph': game_state['original_paragraph'],
                        'encrypted_paragraph':
                        game_state['encrypted_paragraph'],
                        'mapping': game_state['mapping'],
                        'reverse_mapping': game_state['reverse_mapping'],
                        'correctly_guessed': game_state['correctly_guessed'],
                        'mistakes': game_state['mistakes'],
                        'major_attribution': game_state['major_attribution'],
                        'minor_attribution': game_state['minor_attribution'],
                        'is_restored': True
                    }
                    loaded_count += 1
                except Exception as e:
                    logging.error(f"Error loading game state into cache: {e}")

            logging.info(
                f"Initialized game state cache with {loaded_count} active games"
            )
    except Exception as e:
        logging.error(f"Error initializing game state cache: {e}")
