
import os

# Get environment type (development or production)
ENV = os.environ.get('FLASK_ENV', 'development')

# Database path - using different files for dev and prod
if ENV == 'production':
    # Store in project root for production
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prod_game.db')
else:
    # Store in project root for development
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev_game.db')
