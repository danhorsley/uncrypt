
import os
import subprocess
import sys

def run_frontend():
    # Change to the frontend directory
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'my_game', 'frontend')
    
    if not os.path.exists(frontend_dir):
        print(f"Frontend directory not found at {frontend_dir}")
        return
    
    os.chdir(frontend_dir)
    
    # Start the React development server
    print("Starting frontend server...")
    subprocess.run(["npm", "start"], env={**os.environ, "PORT": "3000"})

if __name__ == "__main__":
    run_frontend()
