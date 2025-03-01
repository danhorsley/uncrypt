
#!/bin/bash
# Start the backend server in the background
python run.py &
# Start the frontend
cd my_game/frontend && npm start
