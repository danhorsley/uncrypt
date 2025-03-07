from flask import Flask, jsonify, request, session, render_template
import random
from collections import Counter
import csv
import os
from flask_cors import CORS
import uuid
import logging
import sys
import sqlite3
from .init_db import init_db, update_db_schema
from .login import login_bp
from .login import validate_token

ENV = os.environ.get('FLASK_ENV', 'development')
# Database path - using different files for dev and prod
if ENV == 'production':
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.db')  # Production database
else:
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev_game.db')  # Development database

# Import configuration
try:
    from .config import DATABASE_PATH, ENV
except ImportError:
    # Fallback for direct execution
    from config import DATABASE_PATH, ENV

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ])

game_states = {}

# Initialize the database on startup
init_db()
update_db_schema()

app = Flask(__name__)
# Improved CORS settings with explicit Replit domains
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": [
                "https://*.replit.app",
                "https://*.repl.co",
                "https://*.replit.dev",
                "https://replit.com",
                "https://*.replit.com",
                "https://staging.replit.com",
                "https://firewalledreplit.com",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                #"https://a31dd947-8d2e-46e2-acd6-5467a319da5b-00-3kplm2qa1oqxv.worf.replit.dev"
                "https://f59a0a10-1712-4a08-821f-e6a8198ef815-00-pwp2q7nwy70f.riker.replit.dev",
                "wss://f59a0a10-1712-4a08-821f-e6a8198ef815-00-pwp2q7nwy70f.riker.replit.dev:3000",
                # Include all origins with wildcard as a fallback
                "*"
            ]
        }
    },
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "X-Game-Id"],
    expose_headers=["Access-Control-Allow-Origin", "X-Game-Id"])

app.secret_key = 'your-secret-key'
# Make sure session is permanent
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour in seconds
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow any domain
app.config[
    'SESSION_COOKIE_SAMESITE'] = None  # Required for cross-origin requests
#app.config['SESSION_COOKIE_SECURE'] = True  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
# Register the login blueprint
app.register_blueprint(login_bp)
TOKEN_SECRET = "your-secret-key-change-this-in-production"


class QuoteLoader:

    def __init__(self, csv_path):
        """Load quotes from CSV into memory once."""
        self.quotes = []
        with open(csv_path, 'r', encoding='latin-1') as csvfile:
            reader = csv.DictReader(csvfile)
            self.quotes = [row for row in reader]  # Store the full row

    def get_random_quote(self):
        """Return a random quote with attributions from the loaded list."""
        quote_data = random.choice(self.quotes)
        return {
            "Quote": quote_data["Quote"],
            "Major Attribution": quote_data["Major Attribution"],
            "Minor Attribution": quote_data["Minor Attribution"]
        }


def generate_mapping():
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    shuffled = alphabet.copy()
    random.shuffle(shuffled)
    return dict(zip(alphabet, shuffled))


def encrypt_paragraph(paragraph, mapping):
    return ''.join(mapping.get(char, char) for char in paragraph.upper())


def get_display(encrypted_paragraph, correctly_guessed, reverse_mapping):
    return ''.join(reverse_mapping[char] if char in
                   correctly_guessed else '█' if char.isalpha() else char
                   for char in encrypted_paragraph)


def get_letter_frequency(text):
    """Calculate frequency of each letter in a text."""
    return Counter(c for c in text.upper() if c.isalpha())


def get_unique_letters(text):
    return sorted(set(c for c in text.upper() if c.isalpha()))


# start_game function moved above and modified

recent_logs = []


def log_message(message):
    recent_logs.append(message)
    # Keep only the last 100 logs
    if len(recent_logs) > 100:
        recent_logs.pop(0)
    print(message)  # Also print to console


@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')


@app.route('/health', methods=['GET'])
def health_check():
    logging.info("Health check endpoint accessed")
    return jsonify({"status": "ok", "message": "Service is running"})


@app.route('/debug_logs', methods=['GET'])
def get_logs():
    return jsonify(recent_logs)


@app.route('/debug_client', methods=['POST'])
def debug_client():
    data = request.get_json()
    log_message(f"Debug from client: {data}")
    return jsonify({"status": "logged"})


def start_game(max_length=None):
    # Initialize the quote loader
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'curated.csv')
    quote_loader = QuoteLoader(csv_path)

    # Get a quote that matches the length criteria if specified
    if max_length:
        # Try to find a quote under the maximum length (with a reasonable number of attempts)
        for _ in range(20):  # Try 20 times to find a suitable quote
            quote_data = quote_loader.get_random_quote()
            if len(quote_data["Quote"]) <= max_length:
                break
    else:
        # Get any random quote if no length constraint
        quote_data = quote_loader.get_random_quote()

    paragraph = quote_data["Quote"]

    mapping = generate_mapping()
    reverse_mapping = {v: k for k, v in mapping.items()}
    encrypted = encrypt_paragraph(paragraph, mapping)
    encrypted_frequency = get_letter_frequency(encrypted)
    unique_original_letters = get_unique_letters(paragraph)

    session['game_state'] = {
        'original_paragraph': paragraph,
        'encrypted_paragraph': encrypted,
        'mapping': mapping,
        'reverse_mapping': reverse_mapping,
        'correctly_guessed': [],
        'mistakes': 0,
        'major_attribution': quote_data["Major Attribution"],
        'minor_attribution': quote_data["Minor Attribution"]
    }
    return encrypted, encrypted_frequency, unique_original_letters


@app.route('/start', methods=['GET'])
def start():
    print("==== NEW SHORT GAME STARTING ====")
    # Make session permanent
    session.permanent = True

    # Clear any existing session data to ensure a fresh start
    session.clear()

    # Start a new game with shorter quotes (80 chars should fit on most mobile screens in landscape)
    encrypted, encrypted_frequency, unique_original_letters = start_game(
        max_length=65)

    # Generate a unique game ID
    import uuid
    game_id = str(uuid.uuid4())

    # Store the game state in the in-memory dictionary
    game_states[game_id] = session.get('game_state')

    display = get_display(encrypted, [], {})
    # Extend frequency with 0 for unused letters
    full_frequency = {
        chr(65 + i): encrypted_frequency.get(chr(65 + i), 0)
        for i in range(26)
    }

    ret = {
        'encrypted_paragraph': encrypted,
        'mistakes': 0,
        'letter_frequency':
        full_frequency,  # This should be the frequency of encrypted letters
        'display': display,
        'original_letters': unique_original_letters,
        'major_attribution': '',
        'minor_attribution': '',
        'game_id': game_id
    }

    return jsonify(ret)


@app.route('/longstart', methods=['GET'])
def longstart():
    print("==== NEW LONG GAME STARTING ====")
    # Make session permanent
    session.permanent = True

    # Clear any existing session data to ensure a fresh start
    session.clear()

    # Start a new game with no length restriction
    encrypted, encrypted_frequency, unique_original_letters = start_game()

    # Generate a unique game ID
    import uuid
    game_id = str(uuid.uuid4())

    # Store the game state in the in-memory dictionary
    game_states[game_id] = session.get('game_state')

    display = get_display(encrypted, [], {})
    # Extend frequency with 0 for unused letters
    full_frequency = {
        chr(65 + i): encrypted_frequency.get(chr(65 + i), 0)
        for i in range(26)
    }

    ret = {
        'encrypted_paragraph': encrypted,
        'mistakes': 0,
        'letter_frequency':
        full_frequency,  # This should be the frequency of encrypted letters
        'display': display,
        'original_letters': unique_original_letters,
        'major_attribution': '',
        'minor_attribution': '',
        'game_id': game_id
    }

    return jsonify(ret)


# Then update the guess endpoint to use the game ID
# Update these parts of your app.py


# 1. Modify the guess endpoint to prioritize game_id and prevent session restarts
@app.route('/guess', methods=['POST'])
def guess():
    data = request.get_json()
    logging.debug(f"Received request data for /guess: {data}")

    # Extract game_id from the request body
    game_id = data.get('game_id')
    logging.debug(f"Game ID from request: {game_id}")

    # Also check headers for game_id (this is for the proxy setup)
    if not game_id and request.headers.get('X-Game-Id'):
        game_id = request.headers.get('X-Game-Id')
        logging.debug(f"Game ID from headers: {game_id}")

    # First try to get game state from the game_states dictionary
    game_state = None
    if game_id and game_id in game_states:
        logging.debug(f"Found game state for game_id: {game_id}")
        game_state = game_states[game_id]

    # If not found in dictionary, try the session
    if not game_state:
        game_state = session.get('game_state')
        logging.debug(
            f"Game state from session: {'Found' if game_state else 'Not found'}"
        )

    # If still no game state, we need to create a new game
    if not game_state:
        logging.debug("No game state found - starting new game")
        encrypted, encrypted_frequency, unique_original_letters = start_game()

        # Generate a new game_id
        new_game_id = str(uuid.uuid4())
        game_states[new_game_id] = session.get('game_state')

        return jsonify({
            'display': get_display(encrypted, [], {}),
            'mistakes': 0,
            'correctly_guessed': [],
            'error': 'Session expired, a new game was started',
            'game_id': new_game_id  # Send the new game_id to the client
        })

    # Rest of function remains unchanged
    encrypted_letter = data['encrypted_letter']
    guessed_letter = data['guessed_letter']

    # Process the guess
    if validate_guess(encrypted_letter, guessed_letter,
                      game_state['reverse_mapping'],
                      game_state['correctly_guessed'], game_state['mistakes']):
        # Correct guess
        game_state['mistakes'] = game_state['mistakes']
    else:
        # Incorrect guess
        game_state['mistakes'] += 1

    display = get_display(game_state['encrypted_paragraph'],
                          game_state['correctly_guessed'],
                          game_state['reverse_mapping'])

    # Save state in both session and game_states
    session['game_state'] = game_state
    if game_id:
        game_states[game_id] = game_state

    response_data = {
        'display': display,
        'mistakes': game_state['mistakes'],
        'correctly_guessed': game_state['correctly_guessed']
    }

    logging.debug(f"Returning response: {response_data}")
    return jsonify(response_data)


@app.route('/hint', methods=['POST'])
def hint():
    # Log the received data
    data = request.get_json() or {}
    logging.debug(f"Received request data for /hint: {data}")

    # Extract game_id from the request body
    game_id = data.get('game_id')
    logging.debug(f"Game ID from request body: {game_id}")

    # Also check headers for game_id
    if not game_id and request.headers.get('X-Game-Id'):
        game_id = request.headers.get('X-Game-Id')
        logging.debug(f"Game ID from headers: {game_id}")

    # Initialize game_state as None
    game_state = None

    # First try to get game state from the game_states dictionary
    if game_id and game_id in game_states:
        logging.debug(f"Found game state for game_id: {game_id}")
        game_state = game_states[game_id]

    # If not found in dictionary, try the session
    if not game_state:
        game_state = session.get('game_state')
        logging.debug(
            f"Game state from session: {'Found' if game_state else 'Not found'}"
        )

    if not game_state:
        logging.debug("No game state found - starting new game")
        encrypted, encrypted_frequency, unique_original_letters = start_game()

        # Generate a new game_id
        new_game_id = str(uuid.uuid4())
        game_states[new_game_id] = session.get('game_state')

        # Return the new game with session expired error
        return jsonify({
            'display': get_display(encrypted, [], {}),
            'mistakes': 0,
            'correctly_guessed': [],
            'error': 'Session expired, a new game was started',
            'game_id': new_game_id  # Send the new game_id to the client
        })

    # Process the hint request
    display, mistakes, correctly_guessed = provide_hint(game_state)

    # Save state in both session and game_states
    session['game_state'] = game_state
    if game_id:
        game_states[game_id] = game_state

    # Return the results
    return jsonify({
        'display': display,
        'mistakes': mistakes,
        'correctly_guessed': correctly_guessed
    })


# User and score tracking functions
def register_user(username):
    """Register a new user and return their ID"""
    user_id = str(uuid.uuid4())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (id, username) VALUES (?, ?)',
                           (user_id, username))
            conn.commit()
            return user_id
    except sqlite3.IntegrityError:
        # Username already exists
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?',
                           (username, ))
            result = cursor.fetchone()
            return result['id'] if result else None


def save_game_score(user_id, score, mistakes, completed=True):
    """Save a game score for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO game_scores (user_id, score, mistakes, completed) VALUES (?, ?, ?, ?)',
            (user_id, score, mistakes, completed))
        conn.commit()
        return cursor.lastrowid


def get_user_scores(user_id, limit=10):
    """Get recent scores for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM game_scores WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_leaderboard(limit=10):
    """Get the top scores across all users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT g.*, u.username 
            FROM game_scores g
            JOIN users u ON g.user_id = u.id
            WHERE g.completed = 1
            ORDER BY g.score DESC, g.mistakes ASC
            LIMIT ?
        ''', (limit, ))
        return [dict(row) for row in cursor.fetchall()]


def validate_guess(encrypted_letter, guessed_letter, reverse_mapping,
                   correctly_guessed, mistakes):
    if reverse_mapping[encrypted_letter] == guessed_letter:
        if encrypted_letter not in correctly_guessed:
            correctly_guessed.append(encrypted_letter)
        return True
    return False


def provide_hint(game_state):
    all_encrypted = list(game_state['mapping'].values())
    unmapped = [
        letter for letter in all_encrypted
        if letter not in game_state['correctly_guessed']
    ]
    if unmapped:
        used_n_mapped = [
            x for x in unmapped if x in game_state['encrypted_paragraph']
        ]
        letter = random.choice(used_n_mapped)
        game_state['correctly_guessed'].append(letter)
        game_state['mistakes'] += 1
        r1 = get_display(game_state['encrypted_paragraph'],
                         game_state['correctly_guessed'],
                         game_state['reverse_mapping'])
        r2 = game_state['mistakes']
        r3 = game_state['correctly_guessed']
        print(r1, r2, r3)
        return r1, r2, r3
    return None, game_state['mistakes']


@app.route('/get_attribution', methods=['OPTIONS'])
def options_get_attribution():
    # Handle preflight request for CORS
    response = app.make_default_options_response()
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Game-Id'
    headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@app.route('/get_attribution', methods=['GET'])
def get_attribution():
    # Extract game_id from the request parameters
    game_id = request.args.get('game_id')
    logging.debug(f"Get attribution request for game_id: {game_id}")

    # Also check headers for game_id
    if not game_id and request.headers.get('X-Game-Id'):
        game_id = request.headers.get('X-Game-Id')
        logging.debug(f"Game ID from headers: {game_id}")

    # Initialize game_state as None
    game_state = None

    # First try to get game state from the game_states dictionary
    if game_id and game_id in game_states:
        logging.debug(f"Found game state for game_id: {game_id}")
        game_state = game_states[game_id]

    # If not found in dictionary, try the session
    if not game_state:
        game_state = session.get('game_state')
        logging.debug(
            f"Game state from session: {'Found' if game_state else 'Not found'}"
        )

    # If still no game state, return empty attribution
    if not game_state:
        logging.debug("No game state found for attribution request")
        return jsonify({
            'major_attribution': '',
            'minor_attribution': '',
            'error': 'Game not found or session expired'
        })

    # Return the attribution data
    return jsonify({
        'major_attribution': game_state.get('major_attribution', ''),
        'minor_attribution': game_state.get('minor_attribution', '')
    })


@app.route('/save_quote', methods=['POST'])
def save_quote():
    game_state = session.get('game_state')

    if not game_state:
        return jsonify({'error': 'No active game found'}), 400

    # Extract quote and attribution data
    quote = game_state.get('original_paragraph', '')
    major_attribution = game_state.get('major_attribution', '')
    minor_attribution = game_state.get('minor_attribution', '')

    if not quote:
        return jsonify({'error': 'No quote to save'}), 400

    # File to save to
    csv_path = 'curated.csv'
    file_exists = os.path.isfile(csv_path)

    # Check if quote already exists in the file
    if file_exists:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('Quote') == quote:
                    return jsonify(
                        {'message':
                         'Quote already saved in curated list'}), 200

    # Append the quote to the file
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Quote', 'Major Attribution', 'Minor Attribution']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file didn't exist
        if not file_exists:
            writer.writeheader()

        # Write the quote data
        writer.writerow({
            'Quote': quote,
            'Major Attribution': major_attribution,
            'Minor Attribution': minor_attribution
        })

    return jsonify({'message': 'Quote saved successfully'}), 200
    
@app.route('/record_score', methods=['POST'])
def record_score():
    """
    Record a user's score for a completed game
    Supports both session and token-based authentication
    """
    # Try multiple authentication methods
    user_id = None
    auth_error = None

    # 1. Check session authentication
    if not user_id:
        session_user_id = session.get('user_id')
        if session_user_id:
            user_id = session_user_id
        else:
            auth_error = "Session not found"

    # 2. Check token authentication (in Authorization header)
    if not user_id:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            try:
                user_id = validate_token(token)
            except ValueError as e:
                auth_error = str(e)

    # 3. Check token in request body
    if not user_id:
        data = request.get_json()
        token = data.get('token')
        if token:
            try:
                user_id = validate_token(token)
            except ValueError as e:
                auth_error = str(e)

    # 4. Check explicit user_id in request (least secure, but for testing)
    if not user_id:
        data = request.get_json()
        explicit_user_id = data.get('user_id')
        if explicit_user_id:
            # In production, you might want to verify this user exists
            user_id = explicit_user_id
            logging.warning(f"Using explicit user_id from request: {user_id}")

    # Log what we found
    logging.info(f"Authentication result: user_id={user_id}, error={auth_error}")

    # If no user_id was found through any method, return authentication error
    if not user_id:
        return jsonify({
            "error": "Authentication required", 
            "details": auth_error or "No valid authentication provided"
        }), 401

    # Get data from request
    data = request.get_json()
    game_id = data.get('game_id')
    score = data.get('score', 0)
    mistakes = data.get('mistakes', 0)
    time_taken = data.get('time_taken', 0)  # in seconds
    difficulty = data.get('difficulty', 'normal')

    # Validate the data
    if score < 0 or mistakes < 0 or time_taken < 0:
        return jsonify({"error": "Invalid score data"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Insert the score record
            cursor.execute('''
                INSERT INTO game_scores 
                (user_id, score, mistakes, time_taken, difficulty, is_clean_run, date_played) 
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id, 
                score, 
                mistakes, 
                time_taken, 
                difficulty, 
                mistakes == 0  # is_clean_run is True if no mistakes
            ))

            # Get the ID of the inserted record
            score_id = cursor.lastrowid

            # If there's a game_id, associate it with the score
            if game_id:
                cursor.execute('''
                    UPDATE game_scores 
                    SET game_id = ? 
                    WHERE id = ?
                ''', (game_id, score_id))

            # Update user stats
            cursor.execute('''
                SELECT * FROM user_stats WHERE user_id = ?
            ''', (user_id,))

            user_stats = cursor.fetchone()

            if user_stats:
                # Update existing stats
                cursor.execute('''
                    UPDATE user_stats 
                    SET 
                        total_games_played = total_games_played + 1,
                        cumulative_score = cumulative_score + ?,
                        last_played_date = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (score, user_id))
            else:
                # Create new stats record
                cursor.execute('''
                    INSERT INTO user_stats 
                    (user_id, total_games_played, cumulative_score, last_played_date) 
                    VALUES (?, 1, ?, CURRENT_TIMESTAMP)
                ''', (user_id, score))

            conn.commit()

            logging.info(f"Score recorded successfully for user {user_id}: {score}")

            return jsonify({
                "success": True,
                "score_id": score_id,
                "message": "Score recorded successfully"
            }), 200

    except Exception as e:
        logging.error(f"Error recording score: {e}")
        return jsonify({"error": "Failed to record score"}), 500

if __name__ == '__main__':
    logging.info("Starting application server")
    # In production, debug should be False
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logging.info(f"Debug mode: {debug_mode}")
    logging.info("Running on host: 0.0.0.0, port: 8000")
    app.run(debug=debug_mode, host='0.0.0.0', port=8000)



