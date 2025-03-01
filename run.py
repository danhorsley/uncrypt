from be.app import app

if __name__ == '__main__':
    # You can customize port/host here if needed
    app.run(debug=True, host='0.0.0.0', port=8000)