# CryptoPuzzle

CryptoPuzzle is a daily decryption game inspired by classic cipher puzzles like those in *Covert Action*. Players decrypt encrypted paragraphs using a substitution cipher, guessing letter mappings with an intuitive grid-based UI. The game features a daily challenge, hints, and a retro workstation aesthetic, perfect for puzzle enthusiasts.

## Overview

- **Frontend:** Built with React, providing an interactive UI for guessing letters via grids or keyboard input.
- **Backend:** Powered by Flask (Python), handling encryption, validation, and game logic, running on port 5050.
- **Features:**
  - Daily encrypted paragraphs (currently 5 hardcoded, expandable to Wikipedia/Gutenberg).
  - Click-to-select or keyboard-based letter guessing.
  - Letter frequency sidebar (bars or numbers, toggleable).
  - Hints (costing mistakes), win/loss states, and celebrations.

## Prerequisites

- **Node.js** (v16 or later) for the frontend.
- **Python 3.x** for the backend.
- **npm** (included with Node.js).

## Installation

### 1. Clone the Repository

git clone <your-repo-url>
cd my-game

## 2. Set Up the Backend
Navigate to the backend directory:
bash

cd backend

Install Python dependencies:
bash

pip install -r requirements.txt

Create requirements.txt if not present:

Flask==2.3.2

Ensure Flask runs on port 5050 (see app.py).

## 3. Set Up the Frontend
Navigate to the frontend directory:
bash

cd ../frontend

Install JavaScript dependencies:
bash

npm install

Install additional packages:
bash

npm install react-confetti

## 4. Configure Proxy
Ensure package.json in frontend/ has:
json

"proxy": "http://localhost:5050"

Optionally, set up src/setupProxy.js for explicit proxying (see code for details).

# Running the Game
## 1. Start the Backend
From backend/:
bash

python app.py

Verify it runs on http://localhost:5050.

## 2. Start the Frontend
From frontend/:
bash

npm start

Open http://localhost:3000 in your browser.

