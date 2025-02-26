from flask import Flask, jsonify, request, session
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key'

paragraphs = [
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
    "A JOURNEY OF A THOUSAND MILES BEGINS WITH A SINGLE STEP",
    "CLEOPATRA ASCENDED THE THRONE AT 18 AFTER HER FATHERS DEATH",
    "LEONARDO DA VINCI WAS BORN IN 1452 NEAR FLORENCE",
    "ABRAHAM LINCOLN DELIVERED THE GETTYSBURG ADDRESS IN 1863"
]

def generate_mapping():
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    shuffled = alphabet.copy()
    random.shuffle(shuffled)
    return dict(zip(alphabet, shuffled))

def encrypt_paragraph(paragraph, mapping):
    return ''.join(mapping.get(char, char) for char in paragraph.upper())

def get_display(encrypted_paragraph, correctly_guessed, reverse_mapping):
    return ''.join(reverse_mapping[char] if char in correctly_guessed else char
                   for char in encrypted_paragraph)

def start_game(paragraphs):
    paragraph = random.choice(paragraphs)
    mapping = generate_mapping()
    reverse_mapping = {v: k for k, v in mapping.items()}
    encrypted = encrypt_paragraph(paragraph, mapping)
    session['game_state'] = {
        'original_paragraph': paragraph,
        'encrypted_paragraph': encrypted,
        'mapping': mapping,
        'reverse_mapping': reverse_mapping,
        'correctly_guessed': [],  # Changed to list
        'mistakes': 0
    }
    return encrypted

def validate_guess(encrypted_letter, guessed_letter, reverse_mapping, correctly_guessed, mistakes):
    if reverse_mapping[encrypted_letter] == guessed_letter:
        if encrypted_letter not in correctly_guessed:  # Ensure no duplicates
            correctly_guessed.append(encrypted_letter)
        return True
    return False

def provide_hint(game_state):
    all_encrypted = list(game_state['mapping'].values())
    unmapped = [letter for letter in all_encrypted if letter not in game_state['correctly_guessed']]
    if unmapped:
        letter = random.choice(unmapped)
        game_state['correctly_guessed'].append(letter)
        game_state['mistakes'] += 1
        return get_display(game_state['encrypted_paragraph'],
                          game_state['correctly_guessed'],
                          game_state['reverse_mapping']), game_state['mistakes']
    return None, game_state['mistakes']

@app.route('/start', methods=['GET'])
def start():
    encrypted = start_game(paragraphs)
    return jsonify({'encrypted_paragraph': encrypted, 'mistakes': 0})

@app.route('/guess', methods=['POST'])
def guess():
    data = request.get_json()
    encrypted_letter = data['encrypted_letter']
    guessed_letter = data['guessed_letter']
    game_state = session['game_state']
    
    if validate_guess(encrypted_letter, guessed_letter,
                     game_state['reverse_mapping'],
                     game_state['correctly_guessed'],
                     game_state['mistakes']):
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
        'correctly_guessed': game_state['correctly_guessed']  # Already a list
    })

@app.route('/hint', methods=['POST'])
def hint():
    game_state = session['game_state']
    display, mistakes = provide_hint(game_state)
    session['game_state'] = game_state
    return jsonify({'display': display, 'mistakes': mistakes})

if __name__ == '__main__':
    app.run(debug=True)