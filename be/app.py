from flask import Flask, jsonify, request, session
import random
from collections import Counter
import csv
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials support
app.secret_key = 'your-secret-key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_PATH'] = '/'

paragraphs = [
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
    "A JOURNEY OF A THOUSAND MILES BEGINS WITH A SINGLE STEP", "TEST",
    "LEONARDO DA VINCI WAS BORN IN 1452 NEAR FLORENCE",
    "ABRAHAM LINCOLN DELIVERED THE GETTYSBURG ADDRESS IN 1863"
]


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
                   correctly_guessed else '?' if char.isalpha() else char
                   for char in encrypted_paragraph)


def get_letter_frequency(text):
    return Counter(c for c in text.upper() if c.isalpha())


def get_unique_letters(text):
    return sorted(set(c for c in text.upper() if c.isalpha()))


def start_game():
    # Initialize the quote loader
    #quote_loader = QuoteLoader('quotes.csv')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'curated.csv')
    quote_loader = QuoteLoader(csv_path)
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
    print("new game starting!")
    encrypted, encrypted_frequency, unique_original_letters = start_game()
    print("Game state created and saved to session:", 'game_state' in session)
    display = get_display(encrypted, [], {})
    # Extend frequency with 0 for unused letters
    full_frequency = {
        chr(65 + i): encrypted_frequency.get(chr(65 + i), 0)
        for i in range(26)
    }

    ret = {
        'encrypted_paragraph': encrypted,
        'mistakes': 0,
        'letter_frequency': full_frequency,
        'display': display,
        'original_letters': unique_original_letters,
        # Add empty attributions that will be populated when game is won
        'major_attribution': '',
        'minor_attribution': ''
    }

    return jsonify(ret)


@app.route('/guess', methods=['POST'])
def guess():
    print("guess logged")
    print("Session cookie present:", request.cookies.get('session') is not None)
    print("Session ID:", session.get('_id', 'None'))
    print("Game state in session:", 'game_state' in session)
    
    # Check if game_state exists in the session
    if 'game_state' not in session:
        print("game_state not found in session")
        # If not, start a new game
        encrypted, encrypted_frequency, unique_original_letters = start_game()
        return jsonify({
            'display': get_display(encrypted, [], {}),
            'mistakes': 0,
            'correctly_guessed': [],
            'error': 'Session expired, a new game was started'
        })

    data = request.get_json()
    print("data requested")
    print(data)
    encrypted_letter = data['encrypted_letter']
    guessed_letter = data['guessed_letter']
    game_state = session['game_state']

    if validate_guess(encrypted_letter, guessed_letter,
                      game_state['reverse_mapping'],
                      game_state['correctly_guessed'], game_state['mistakes']):
        game_state['mistakes'] = game_state['mistakes']
    else:
        game_state['mistakes'] += 1

    display = get_display(game_state['encrypted_paragraph'],
                          game_state['correctly_guessed'],
                          game_state['reverse_mapping'])
    session['game_state'] = game_state
    return jsonify({
        'display': display,
        'mistakes': game_state['mistakes'],
        'correctly_guessed': game_state['correctly_guessed']
    })


@app.route('/hint', methods=['POST'])
def hint():
    # Check if game_state exists in the session
    if 'game_state' not in session:
        # If not, start a new game
        encrypted, encrypted_frequency, unique_original_letters = start_game()
        return jsonify({
            'display': get_display(encrypted, [], {}),
            'mistakes': 0,
            'correctly_guessed': [],
            'error': 'Session expired, a new game was started'
        })

    game_state = session['game_state']
    display, mistakes, correctly_guessed = provide_hint(game_state)
    session['game_state'] = game_state
    return jsonify({
        'display': display,
        'mistakes': mistakes,
        'correctly_guessed': correctly_guessed
    })


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


@app.route('/get_attribution', methods=['GET'])
def get_attribution():
    game_state = session['game_state']

    # Check if the game is completed (all letters guessed)
    encrypted = game_state['encrypted_paragraph']
    unique_encrypted_letters = len(set(c for c in encrypted if c.isalpha()))
    correctly_guessed = game_state['correctly_guessed']

    # Only return the attribution if the game is won
    if len(correctly_guessed) >= unique_encrypted_letters:
        return jsonify({
            'major_attribution': game_state['major_attribution'],
            'minor_attribution': game_state['minor_attribution']
        })
    else:
        return jsonify({'error': 'Game not completed yet'}), 400


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
