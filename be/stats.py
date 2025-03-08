# stats.py - User stats and leaderboard related functionality
from flask import Blueprint, request, jsonify, session
import logging
import datetime
from .init_db import get_db_connection
from .login import validate_token

# Create a blueprint for the stats routes
stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/user_stats', methods=['GET'])
def get_user_stats():
    # Get user_id from token validation or session
    auth_header = request.headers.get('Authorization')
    user_id = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            user_id = validate_token(token)
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

    # If no token or invalid token, check session
    if not user_id:
        user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get the user's stats from user_stats table
            cursor.execute('''
                SELECT * FROM user_stats
                WHERE user_id = ?
            ''', (user_id,))

            stats = cursor.fetchone()

            # If no stats exist yet, initialize with defaults
            if not stats:
                return jsonify({
                    "user_id": user_id,
                    "current_streak": 0,
                    "max_streak": 0,
                    "current_noloss_streak": 0,
                    "max_noloss_streak": 0,
                    "total_games_played": 0,
                    "cumulative_score": 0,
                    "highest_weekly_score": 0,
                    "last_played_date": None,
                    "weekly_stats": {
                        "score": 0,
                        "games_played": 0
                    }
                })

            # Calculate weekly stats on-the-fly
            # Get the start of the current week (Monday)
            today = datetime.datetime.now().date()
            start_of_week = today - datetime.timedelta(days=today.weekday())

            cursor.execute('''
                SELECT SUM(score) as weekly_score
                FROM game_scores
                WHERE user_id = ? 
                AND date(created_at) >= date(?)
            ''', (user_id, start_of_week))

            weekly_data = cursor.fetchone()
            weekly_score = weekly_data['weekly_score'] if weekly_data and weekly_data['weekly_score'] is not None else 0

            # Update highest_weekly_score if current weekly score is higher
            if stats:
                stats_dict = dict(stats)
                highest_weekly_score = stats_dict.get('highest_weekly_score', 0)
                if weekly_score > highest_weekly_score:
                    highest_weekly_score = weekly_score
            else:
                highest_weekly_score = weekly_score
            # Get top 5 scores for personal stats
            cursor.execute('''
                SELECT score, difficulty, time_taken, created_at 
                FROM game_scores
                WHERE user_id = ? AND completed = 1
                ORDER BY score DESC
                LIMIT 5
            ''', (user_id,))

            top_scores = []
            for row in cursor.fetchall():
                top_scores.append({
                    "score": row['score'],
                    "difficulty": row['difficulty'],
                    "time_taken": row['time_taken'],
                    "date": row['created_at']
                })

            # Prepare the response
            response = {
                "user_id": user_id,
                "current_streak": stats['current_streak'],
                "max_streak": stats['max_streak'],
                "current_noloss_streak": stats.get('current_noloss_streak', 0),
                "max_noloss_streak": stats.get('max_noloss_streak', 0),
                "total_games_played": stats['total_games_played'],
                "cumulative_score": stats['cumulative_score'],
                "highest_weekly_score": stats.get('highest_weekly_score', 
                                              stats.get('highest_monthly_score', 0)),
                "last_played_date": stats['last_played_date'],
                "weekly_stats": weekly_stats,
                "top_scores": top_scores
            }

            return jsonify(response)

    except Exception as e:
        logging.error(f"Error getting user stats: {e}")
        return jsonify({"error": "Failed to retrieve user statistics"}), 500

@stats_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # Extract parameters with defaults
    period = request.args.get('period', 'all-time')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 50)  # Limit to 50 max

    # Calculate pagination offset
    offset = (page - 1) * per_page

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get the requesting user's ID (if authenticated)
            auth_header = request.headers.get('Authorization')
            user_id = None

            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    user_id = validate_token(token)
                except ValueError:
                    # Continue anyway, just won't have user-specific data
                    pass

            # If no token, try session
            if not user_id:
                user_id = session.get('user_id')

            # Define the time filter condition
            time_filter = ""
            time_filter_params = []

            # Modify query based on requested period
            if period == 'weekly':
                # Get start of current week (Monday)
                today = datetime.datetime.now().date()
                start_of_week = today - datetime.timedelta(days=today.weekday())
                time_filter = "AND date(g.created_at) >= date(?)"
                time_filter_params = [start_of_week.isoformat()]

            # Base query for leaderboard
            leaderboard_query = '''
                SELECT 
                    u.username, 
                    u.user_id,
                    SUM(g.score) as total_score,
                    COUNT(g.id) as games_played,
                    AVG(g.score) as avg_score
                FROM game_scores g
                JOIN users u ON g.user_id = u.user_id
                WHERE g.completed = 1
            '''

            if time_filter:
                leaderboard_query += " " + time_filter

            leaderboard_query += '''
                GROUP BY g.user_id
                ORDER BY total_score DESC
                LIMIT ? OFFSET ?
            '''

            # Execute query for leaderboard entries
            params = time_filter_params + [per_page, offset]
            cursor.execute(leaderboard_query, params)

            entries = []
            for idx, row in enumerate(cursor.fetchall()):
                entries.append({
                    "rank": offset + idx + 1,  # Calculate rank based on pagination
                    "username": row['username'],
                    "user_id": row['user_id'],
                    "score": row['total_score'],
                    "games_played": row['games_played'],
                    "avg_score": round(row['avg_score'], 1) if row['avg_score'] else 0,
                    "is_current_user": row['user_id'] == user_id
                })

            # Get total number of entries for pagination info
            count_query = '''
                SELECT COUNT(DISTINCT g.user_id) 
                FROM game_scores g
                JOIN users u ON g.user_id = u.user_id
                WHERE g.completed = 1
            '''

            if time_filter:
                count_query += " " + time_filter

            cursor.execute(count_query, time_filter_params)
            total_users = cursor.fetchone()[0]

            # If authenticated, get current user's rank even if not in results
            user_rank = None
            if user_id:
                rank_query = '''
                    WITH RankedUsers AS (
                        SELECT 
                            user_id, 
                            RANK() OVER (ORDER BY SUM(score) DESC) as user_rank
                        FROM game_scores
                        WHERE completed = 1
                '''

                if time_filter:
                    # Remove the 'g.' prefix since we're not using an alias in this query
                    modified_time_filter = time_filter.replace('g.', '')
                    rank_query += " " + modified_time_filter

                rank_query += '''
                        GROUP BY user_id
                    )
                    SELECT user_rank FROM RankedUsers WHERE user_id = ?
                '''

                try:
                    # Try the query with window functions first
                    cursor.execute(rank_query, time_filter_params + [user_id])
                    rank_result = cursor.fetchone()
                    if rank_result:
                        user_rank = rank_result[0]
                except Exception as e:
                    # If window functions aren't supported, fall back to a simpler approach
                    logging.warning(f"Window function not supported, using fallback method: {e}")

                    # Fallback method for SQLite that doesn't support window functions
                    fallback_query = '''
                        SELECT COUNT(*) + 1 FROM (
                            SELECT user_id, SUM(score) as total_score
                            FROM game_scores
                            WHERE completed = 1
                    '''

                    if time_filter:
                        fallback_query += " " + time_filter.replace('g.', '')

                    fallback_query += '''
                            GROUP BY user_id
                        ) scores
                        WHERE total_score > (
                            SELECT SUM(score) FROM game_scores 
                            WHERE user_id = ? AND completed = 1
                    '''

                    if time_filter:
                        fallback_query += " " + time_filter.replace('g.', '')

                    fallback_query += ")"

                    cursor.execute(fallback_query, time_filter_params + [user_id] + time_filter_params)
                    user_rank = cursor.fetchone()[0]

            # Return results
            return jsonify({
                "period": period,
                "page": page,
                "per_page": per_page,
                "total_users": total_users,
                "total_pages": (total_users + per_page - 1) // per_page,
                "entries": entries,
                "user_rank": user_rank
            })

    except Exception as e:
        logging.error(f"Error fetching leaderboard: {e}")
        return jsonify({"error": "Failed to retrieve leaderboard data"}), 500