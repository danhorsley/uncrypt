# scoring.py - Score recording and statistics management
from flask import Blueprint, request, jsonify, session
import logging
import datetime
from .init_db import get_db_connection
from .login import validate_token

# Create a blueprint for the scoring routes
scoring_bp = Blueprint('scoring', __name__)

@scoring_bp.route('/record_score', methods=['POST'])
def record_score():
    # Get user from token or session
    auth_header = request.headers.get('Authorization')
    user_id = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            user_id = validate_token(token)
        except Exception as e:
            print(f"Token validation failed: {e}")

    if not user_id:
        print("if not user_id triggered")
        user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Authentication required", "code": "auth_required"}), 401

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

    # Determine if the game was won or lost
    max_mistakes = data.get('max_mistakes', 5)  # Default to normal difficulty
    is_win = mistakes < max_mistakes

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check for existing score
            if game_type == 'daily' and challenge_date:
                cursor.execute('''
                    SELECT id FROM game_scores 
                    WHERE user_id = ? AND game_type = 'daily' AND challenge_date = ?
                ''', (user_id, challenge_date))
            else:
                cursor.execute('''
                    SELECT id FROM game_scores 
                    WHERE user_id = ? AND game_id = ?
                ''', (user_id, game_id))

            existing_score = cursor.fetchone()
            if existing_score:
                return jsonify({
                    "success": True,
                    "message": f"Score was already recorded for this {game_type} game",
                    "score_id": existing_score['id'],  # Access it like a dictionary
                    "duplicate": True
                }), 200

            # Record the new score
            cursor.execute('''
                INSERT INTO game_scores (
                    user_id, game_id, score, mistakes, time_taken, 
                    difficulty, game_type, challenge_date, completed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, game_id, score, mistakes, time_taken,
                difficulty, game_type, challenge_date, is_win
            ))

            score_id = cursor.lastrowid
            print("score_id : ",score_id)
            # Get user's current stats
            cursor.execute('''
                SELECT * FROM user_stats
                WHERE user_id = ?
            ''', (user_id,))

            stats = cursor.fetchone()
            print("stats", stats)
            # Default values if no stats exist
            if not stats:
                stats = {
                    'current_streak': 0,
                    'max_streak': 0,
                    'current_noloss_streak': 0,
                    'max_noloss_streak': 0,
                    'total_games_played': 0,
                    'cumulative_score': 0,
                    'highest_weekly_score': 0
                }

            # Prepare updates to user_stats
            total_games_played = (stats['total_games_played'] if stats else 0) + 1
            cumulative_score = (stats['cumulative_score'] if stats else 0) + score
            # Calculate streaks
            current_streak = (stats['current_streak'] if stats else 0) 
            max_streak = (stats['max_streak'] if stats else 0) 
            current_noloss_streak = (stats['current_noloss_streak'] if stats else 0) 
            max_noloss_streak = (stats['max_noloss_streak'] if stats else 0) 
            # With this corrected version:
            if not stats:
                # No existing stats, use defaults
                total_games_played = 1
                cumulative_score = score
                current_streak = 1 if is_win else 0
                max_streak = 1 if is_win else 0
                current_noloss_streak = 1 if mistakes < max_mistakes else 0
                max_noloss_streak = 1 if mistakes < max_mistakes else 0
                highest_weekly_score = weekly_score if weekly_score > 0 else 0
                # "user_id | current_streak | max_streak | current_noloss_streak | max_noloss_streak | total_games_played | cumulative_score | highest_weekly_score | last_played_date"
            else:
                # We have existing stats, need to access them safely
                # Convert sqlite3.Row to a regular dictionary first
                stats_dict = dict(stats)

                # Now use the dictionary with .get() method
                total_games_played = stats_dict.get('total_games_played', 0) + 1
                cumulative_score = stats_dict.get('cumulative_score', 0) + score

                # Calculate streaks
                current_streak = stats_dict.get('current_streak', 0)
                max_streak = stats_dict.get('max_streak', 0)
                current_noloss_streak = stats_dict.get('current_noloss_streak', 0)
                max_noloss_streak = stats_dict.get('max_noloss_streak', 0)
                highest_weekly_score = stats_dict.get('highest_weekly_score', 0)
                # print("second round of gets triggered")
                # Update streak calculations
                if is_win:
                    current_streak += 1
                    if current_streak > max_streak:
                        max_streak = current_streak
                else:
                    current_streak = 0

                # Handle no-loss streak
                if mistakes < max_mistakes:
                    current_noloss_streak += 1
                    if current_noloss_streak > max_noloss_streak:
                        max_noloss_streak = current_noloss_streak
                else:
                    current_noloss_streak = 0

            # Calculate weekly score
            today = datetime.datetime.now().date()
            start_of_week = today - datetime.timedelta(days=today.weekday())

            cursor.execute('''
                SELECT SUM(score) as weekly_score
                FROM game_scores
                WHERE user_id = ? 
                AND date(created_at) >= date(?)
            ''', (user_id, start_of_week))

            weekly_data = cursor.fetchone()
            weekly_score = weekly_data['weekly_score'] if weekly_data and weekly_data['weekly_score'] else 0

            # Update highest_weekly_score if current weekly score is higher
            highest_weekly_score = (stats['highest_weekly_score'] if stats else 0)
            if weekly_score > highest_weekly_score:
                highest_weekly_score = weekly_score

            # Check if user_stats record exists
            if 'user_id':
                # Update existing stats
                cursor.execute('''
                    UPDATE user_stats 
                    SET 
                        current_streak = ?,
                        max_streak = ?,
                        current_noloss_streak = ?,
                        max_noloss_streak = ?,
                        total_games_played = ?,
                        cumulative_score = ?,
                        highest_weekly_score = ?,
                        last_played_date = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (
                    current_streak, max_streak, 
                    current_noloss_streak, max_noloss_streak,
                    total_games_played, cumulative_score, 
                    highest_weekly_score, user_id
                ))
            else:
                # Create new stats record
                cursor.execute('''
                    INSERT INTO user_stats (
                        user_id, current_streak, max_streak, 
                        current_noloss_streak, max_noloss_streak,
                        total_games_played, cumulative_score, 
                        highest_weekly_score, last_played_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id, current_streak, max_streak,
                    current_noloss_streak, max_noloss_streak,
                    total_games_played, cumulative_score,
                    highest_weekly_score
                ))

            conn.commit()

            # Return success response with updated stats
            return jsonify({
                "success": True,
                "message": f"{game_type.capitalize()} score recorded successfully",
                "score_id": score_id,
                "stats_updated": {
                    "current_streak": current_streak,
                    "max_streak": max_streak,
                    "current_noloss_streak": current_noloss_streak,
                    "max_noloss_streak": max_noloss_streak,
                    "total_games_played": total_games_played,
                    "cumulative_score": cumulative_score,
                    "weekly_score": weekly_score
                }
            }), 201

    except Exception as e:
        logging.error(f"Error recording score: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to record score due to server error"
        }), 500