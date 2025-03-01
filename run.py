
from be.app import app

if __name__ == '__main__':
    # Increasing session lifetime and ensuring cookies work across all domains
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Changed from 'Lax' to allow cross-origin requests
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    
    # Debug mode with clear messages
    app.run(debug=True, host='0.0.0.0', port=8000)
