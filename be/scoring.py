# scoring.py - Score recording and statistics management
from flask import Blueprint, request, jsonify, session
import logging
import datetime
from .init_db import get_db_connection
from .login import validate_token
from .game_state import delete_game_state  # Import the new function

# Create a blueprint for the scoring routes
scoring_bp = Blueprint('scoring', __name__)


@scoring_bp.route('/record_score', methods=['POST'])
def record_score():
    print("recordscore triggered")

    # Get data from request
    data = request.get_json()
    game_id = data.get('game_id')

    # Try to get user from session first
    user_id = session.get('user_id')

    # If not in session, check for token in Authorization header
    if not user_id:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Use the validate_token function from login.py
                user_id = validate_token(token)
                print(f"Authenticated via token: user_id={user_id}")
            except Exception as e:
                print(f"Token validation failed: {e}")

    print("user_id", user_id)

    if not user_id:
        return jsonify({
            "error": "Authentication required",
            "code": "auth_required"
        }), 401

    # Get data from request
    data = request.get_json()
    game_id = data.get('game_id')

    # Validate required fields
    if not game_id:
        return jsonify({"error": "Missing game_id"}), 400

    # Extract game data
    game_type = data.get('game_type', 'regular')
    challenge_date = data.get('challenge_date')
    score = data.get('score', 0)
    mistakes = data.get('mistakes', 0)
    time_taken = data.get('time_taken', 0)
    difficulty = data.get('difficulty', 'normal')

    # Use the completed flag directly, defaulting to False
    completed = bool(data.get('completed', False))

    # Log request for debugging
    logging.info(
        f"Record score request: user={user_id}, game={game_id}, type={game_type}, score={score}, completed={completed}"
    )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Insert the score record
            cursor.execute(
                '''
                INSERT INTO game_scores (
                    user_id, game_id, score, mistakes, time_taken, 
                    difficulty, game_type, challenge_date, completed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, game_id, score, mistakes, time_taken, difficulty,
                  game_type, challenge_date, completed))

            score_id = cursor.lastrowid

            # Get user's current stats
            cursor.execute(
                '''
                SELECT * FROM user_stats
                WHERE user_id = ?
            ''', (user_id, ))

            stats = cursor.fetchone()

            # Initialize default stats if none exist
            if not stats:
                # Calculate aggregated stats from all existing scores
                cursor.execute(
                    '''
                    SELECT COUNT(*) as total_games, SUM(score) as total_score
                    FROM game_scores
                    WHERE user_id = ?
                ''', (user_id, ))

                games_data = cursor.fetchone()
                total_games = games_data['total_games'] if games_data else 1
                total_score = games_data[
                    'total_score'] if games_data and games_data[
                        'total_score'] is not None else score

                # Default values for new stats
                stats_dict = {
                    'current_streak': 0,
                    'max_streak': 0,
                    'current_noloss_streak': 0,
                    'max_noloss_streak': 0,
                    'total_games_played': total_games,
                    'cumulative_score': total_score,
                    'highest_weekly_score': 0
                }
            else:
                # Convert to dictionary for easier handling
                stats_dict = dict(stats)

            # Update streak calculations based on win status (using completed flag)
            current_streak = stats_dict.get('current_streak', 0)
            max_streak = stats_dict.get('max_streak', 0)
            current_noloss_streak = stats_dict.get('current_noloss_streak', 0)
            max_noloss_streak = stats_dict.get('max_noloss_streak', 0)

            # Win streak updates - increment on win, reset on loss
            if completed:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
            else:
                # Reset streak on loss
                current_streak = 0

            # No-loss streak updates - reset only on explicit loss
            if not completed:
                # Reset on explicit loss
                current_noloss_streak = 0
            else:
                current_noloss_streak += 1
                if current_noloss_streak > max_noloss_streak:
                    max_noloss_streak = current_noloss_streak

            # Insert or update user_stats
            if not stats:
                # Create new stats record
                cursor.execute(
                    '''
                    INSERT INTO user_stats (
                        user_id, current_streak, max_streak, 
                        current_noloss_streak, max_noloss_streak,
                        total_games_played, cumulative_score, 
                        highest_weekly_score, last_played_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, current_streak, max_streak,
                      current_noloss_streak, max_noloss_streak,
                      stats_dict['total_games_played'],
                      stats_dict['cumulative_score'],
                      stats_dict['highest_weekly_score']))
            else:
                # Update existing stats
                cursor.execute(
                    '''
                    UPDATE user_stats 
                    SET 
                        current_streak = ?,
                        max_streak = ?,
                        current_noloss_streak = ?,
                        max_noloss_streak = ?,
                        total_games_played = total_games_played + 1,
                        cumulative_score = cumulative_score + ?,
                        last_played_date = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (current_streak, max_streak, current_noloss_streak,
                      max_noloss_streak, score, user_id))

            conn.commit()

            # Now that score is recorded, delete the active game state
            # This game is considered complete whether win or loss
            if user_id:
                delete_game_state(user_id=user_id)
            else:
                delete_game_state(game_id=game_id)

            return {
                "success": True,
                "score_id": score_id,
                "streak_updated": {
                    "current_streak": current_streak,
                    "max_streak": max_streak,
                    "current_noloss_streak": current_noloss_streak,
                    "max_noloss_streak": max_noloss_streak
                }
            }

    except Exception as e:
        logging.error(f"Error recording score: {e}")
        return {"success": False, "error": f"Failed to record score: {str(e)}"}
