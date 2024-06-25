from flask import Flask, render_template, redirect, url_for, request, jsonify
from authlib.integrations.flask_client import OAuth
from amadeus import Client, ResponseError
from config import Config
import requests

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config.from_object(Config)

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid profile email'},
)

# Amadeus client setup
amadeus = Client(
    client_id=Config.AMADEUS_CLIENT_ID,
    client_secret=Config.AMADEUS_CLIENT_SECRET
)

# Function to get chatbot response (replace with your actual AI service integration)
def get_chatbot_response(message):
    ai_url = 'https://api.youraiservice.com/chatbot'
    headers = {
        'Authorization': f'Bearer {Config.OPENAI_API_KEY}'  # Use f-string for clarity
    }
    data = {
        'query': message,
        'sessionId': 'user_session_id'  # Optionally use a session ID to track conversations
    }
    try:
        response = requests.post(ai_url, headers=headers, json=data)
        reply = response.json()
        return reply.get('response')
    except Exception as e:
        return {'error': str(e)}

# Routes
@app.route('/')
def index():
    return render_template('index.htm')

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/callback')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    # User info contains the user's Google profile. Use it to create a user session.
    return jsonify(user_info)

@app.route('/features')
def features():
    return render_template('features.html')  


def search_flights(origin, destination, date):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1
        ).data
        return response
    except ResponseError as error:
        return {'error': str(error)}

@app.route('/search_flights', methods=['GET'])
def get_flights():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')
    flights = search_flights(origin, destination, date)
    return jsonify(flights)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if request.method == 'POST':
        message = request.json.get('message')
        if message:
            bot_response = get_chatbot_response(message)
            return jsonify({'response': bot_response})
        else:
            return jsonify({'error': 'No message provided'}), 400
    else:
        return jsonify({'error': 'Method not allowed'}), 405

if __name__ == '__main__':
    app.run(debug=True)
