from webapp import create_app

# Create Flask app instance
app = create_app()

# Vercel expects the app to be exported as 'app'
# This is already done above, but we can also export it explicitly if needed
if __name__ == "__main__":
    app.run(debug=True, port=5000, host='127.0.0.1')

