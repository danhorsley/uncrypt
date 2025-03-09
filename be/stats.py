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

            stats_row = cursor.fetchone()

            # If no stats exist yet, initialize with defaults
            if not stats_row:
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
                    },
                    "top_scores": []
                })

            # Convert the row to a dictionary
            stats_dict = dict(stats_row)

            # Calculate weekly stats on-the-fly
            # Get the start of the current week (Monday)
            today = datetime.datetime.now().date()
            start_of_week = today - datetime.timedelta(days=today.weekday())

            cursor.execute('''
                SELECT SUM(score) as weekly_score, COUNT(*) as games_count
                FROM game_scores
                WHERE user_id = ? 
                AND date(created_at) >= date(?)
            ''', (user_id, start_of_week))

            weekly_data = cursor.fetchone()

            weekly_score = weekly_data['weekly_score'] if weekly_data and weekly_data['weekly_score'] is not None else 0
            weekly_games = weekly_data['games_count'] if weekly_data and weekly_data['games_count'] is not None else 0

            # Prepare weekly stats
            weekly_stats = {
                "score": weekly_score,
                "games_played": weekly_games
            }

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
                "current_streak": stats_dict.get('current_streak', 0),
                "max_streak": stats_dict.get('max_streak', 0),
                "current_noloss_streak": stats_dict.get('current_noloss_streak', 0),
                "max_noloss_streak": stats_dict.get('max_noloss_streak', 0),
                "total_games_played": stats_dict.get('total_games_played', 0),
                "cumulative_score": stats_dict.get('cumulative_score', 0),
                "highest_weekly_score": stats_dict.get('highest_weekly_score', 
                                              stats_dict.get('highest_monthly_score', 0)),
                "last_played_date": stats_dict.get('last_played_date'),
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
    per_page = min(int(request.args.get('per_page', 10)), 50)  # Limit to 50 max

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

            # Base query for top entries
            if period == 'weekly':
                # If weekly, we need to calculate from game_scores
                top_entries_query = '''
                    SELECT 
                        u.username, 
                        u.user_id,
                        SUM(g.score) as total_score,
                        COUNT(g.id) as games_played,
                        AVG(g.score) as avg_score,
                        u.user_id = ? as is_current_user,
                        RANK() OVER (ORDER BY SUM(g.score) DESC) as rank
                    FROM game_scores g
                    JOIN users u ON g.user_id = u.user_id
                    WHERE g.completed = 1
                '''

                if time_filter:
                    top_entries_query += " " + time_filter

                top_entries_query += '''
                    GROUP BY g.user_id
                    ORDER BY total_score DESC
                    LIMIT ? OFFSET ?
                '''
                top_entries_params = [user_id] + time_filter_params + [per_page, offset]
            else:
                # For all-time, use the user_stats table which has precomputed values
                top_entries_query = '''
                    SELECT 
                        u.username, 
                        u.user_id,
                        s.cumulative_score as total_score,
                        s.total_games_played as games_played,
                        CASE 
                            WHEN s.total_games_played > 0 THEN s.cumulative_score / s.total_games_played 
                            ELSE 0 
                        END as avg_score,
                        u.user_id = ? as is_current_user,
                        RANK() OVER (ORDER BY s.cumulative_score DESC) as rank
                    FROM user_stats s
                    JOIN users u ON s.user_id = u.user_id
                    ORDER BY total_score DESC
                    LIMIT ? OFFSET ?
                '''
                top_entries_params = [user_id, per_page, offset]

            # Execute query for top leaderboard entries
            cursor.execute(top_entries_query, top_entries_params)
            top_entries = []
            for row in cursor.fetchall():
                top_entries.append({
                    "rank": row['rank'],
                    "username": row['username'],
                    "user_id": row['user_id'],
                    "score": row['total_score'],
                    "games_played": row['games_played'],
                    "avg_score": round(row['avg_score'], 1) if row['avg_score'] else 0,
                    "is_current_user": bool(row['is_current_user'])
                })

            # Get current user entry if authenticated and not in top entries
            current_user_entry = None
            if user_id and not any(entry['is_current_user'] for entry in top_entries):
                if period == 'weekly':
                    user_query = '''
                        SELECT 
                            u.username, 
                            u.user_id,
                            SUM(g.score) as total_score,
                            COUNT(g.id) as games_played,
                            AVG(g.score) as avg_score,
                            RANK() OVER (ORDER BY SUM(g.score) DESC) as rank
                        FROM game_scores g
                        JOIN users u ON g.user_id = u.user_id
                        WHERE g.completed = 1
                        AND u.user_id = ?
                    '''
                    if time_filter:
                        user_query += " " + time_filter.replace('g.', '')
                    user_query += " GROUP BY g.user_id"
                    user_params = [user_id] + time_filter_params
                else:
                    # For all-time, get from user_stats
                    user_query = '''
                        WITH RankedUsers AS (
                            SELECT 
                                u.user_id,
                                u.username,
                                s.cumulative_score as total_score,
                                s.total_games_played as games_played,
                                CASE 
                                    WHEN s.total_games_played > 0 THEN s.cumulative_score / s.total_games_played 
                                    ELSE 0 
                                END as avg_score,
                                RANK() OVER (ORDER BY s.cumulative_score DESC) as rank
                            FROM user_stats s
                            JOIN users u ON s.user_id = u.user_id
                        )
                        SELECT * FROM RankedUsers WHERE user_id = ?
                    '''
                    user_params = [user_id]

                cursor.execute(user_query, user_params)
                user_row = cursor.fetchone()

                if user_row:
                    current_user_entry = {
                        "rank": user_row['rank'],
                        "username": user_row['username'],
                        "user_id": user_row['user_id'],
                        "score": user_row['total_score'],
                        "games_played": user_row['games_played'],
                        "avg_score": round(user_row['avg_score'], 1) if user_row['avg_score'] else 0,
                        "is_current_user": True
                    }

            # Get total number of entries for pagination info
            if period == 'weekly':
                count_query = '''
                    SELECT COUNT(DISTINCT g.user_id) as total_users
                    FROM game_scores g
                    JOIN users u ON g.user_id = u.user_id
                    WHERE g.completed = 1
                '''

                if time_filter:
                    count_query += " " + time_filter

                cursor.execute(count_query, time_filter_params)
            else:
                # For all-time, count from user_stats
                count_query = 'SELECT COUNT(*) as total_users FROM user_stats'
                cursor.execute(count_query)

            total_users = cursor.fetchone()['total_users']

            # Prepare pagination info
            pagination = {
                "current_page": page,
                "total_pages": (total_users + per_page - 1) // per_page if total_users > 0 else 1,
                "total_entries": total_users,
                "per_page": per_page
            }

            # Return results in the new format
            return jsonify({
                "topEntries": top_entries,
                "currentUserEntry": current_user_entry,
                "pagination": pagination,
                "period": period
            })

    except Exception as e:
        logging.error(f"Error fetching leaderboard: {e}")
        return jsonify({"error": "Failed to retrieve leaderboard data"}), 500

@stats_bp.route('/streak_leaderboard', methods=['GET'])
def get_streak_leaderboard():
    # Extract parameters with defaults
    streak_type = request.args.get('type', 'win')  # 'win' or 'noloss'
    period = request.args.get('period', 'current') # 'current' or 'best'
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 50)  # Limit to 50 max

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

            # Determine which streak field to use based on parameters
            streak_field = ""
            if streak_type == 'win':
                streak_field = "current_streak" if period == 'current' else "max_streak"
            else:  # 'noloss'
                streak_field = "current_noloss_streak" if period == 'current' else "max_noloss_streak"

            # Base query for top streak entries
            streak_query = f'''
                SELECT 
                    u.username, 
                    u.user_id,
                    s.{streak_field} as streak_length,
                    s.last_played_date,
                    u.user_id = ? as is_current_user,
                    RANK() OVER (ORDER BY s.{streak_field} DESC, s.last_played_date DESC) as rank
                FROM user_stats s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.{streak_field} > 0
                ORDER BY s.{streak_field} DESC, s.last_played_date DESC
                LIMIT ? OFFSET ?
            '''

            # Execute query for top streak entries
            cursor.execute(streak_query, [user_id, per_page, offset])
            top_entries = []
            for row in cursor.fetchall():
                entry = {
                    "rank": row['rank'],
                    "username": row['username'],
                    "user_id": row['user_id'],
                    "streak_length": row['streak_length'],
                    "is_current_user": bool(row['is_current_user'])
                }

                # Only include last_active for current streaks
                if period == 'current':
                    entry["last_active"] = row['last_played_date']

                top_entries.append(entry)

            # Get current user entry if authenticated and not in top entries
            current_user_entry = None
            if user_id and not any(entry['is_current_user'] for entry in top_entries):
                user_query = f'''
                    WITH RankedUsers AS (
                        SELECT 
                            u.user_id,
                            u.username,
                            s.{streak_field} as streak_length,
                            s.last_played_date,
                            RANK() OVER (ORDER BY s.{streak_field} DESC, s.last_played_date DESC) as rank
                        FROM user_stats s
                        JOIN users u ON s.user_id = u.user_id
                        WHERE s.{streak_field} > 0
                    )
                    SELECT * FROM RankedUsers WHERE user_id = ?
                '''
                cursor.execute(user_query, [user_id])
                user_row = cursor.fetchone()

                if user_row:
                    current_user_entry = {
                        "rank": user_row['rank'],
                        "username": user_row['username'],
                        "user_id": user_row['user_id'],
                        "streak_length": user_row['streak_length'],
                        "is_current_user": True
                    }

                    # Only include last_active for current streaks
                    if period == 'current':
                        current_user_entry["last_active"] = user_row['last_played_date']

            # Get total number of users with streaks > 0
            count_query = f'''
                SELECT COUNT(*) as total_users
                FROM user_stats 
                WHERE {streak_field} > 0
            '''
            cursor.execute(count_query)
            total_users = cursor.fetchone()['total_users']

            # Prepare pagination info
            pagination = {
                "current_page": page,
                "total_pages": (total_users + per_page - 1) // per_page if total_users > 0 else 1,
                "total_entries": total_users,
                "per_page": per_page
            }

            # Return results in the new format
            return jsonify({
                "entries": top_entries,  # Keep original name for streak endpoints
                "currentUserEntry": current_user_entry,
                "pagination": pagination,
                "streak_type": streak_type,
                "period": period
            })

    except Exception as e:
        logging.error(f"Error fetching streak leaderboard: {e}")
        return jsonify({"error": "Failed to retrieve streak leaderboard data"}), 500