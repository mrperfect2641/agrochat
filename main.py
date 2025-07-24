from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from models import db, User, ChatMessage
from NLP import AgricultureNLP
from rain_pred import RainPredictor
from crop_pred import CropPredictor
import requests
import os
import re
from datetime import datetime, timedelta
from flask_mail import Mail, Message

app = Flask(__name__, static_folder='.')
app.config.update(
    SECRET_KEY='2641',
    SQLALCHEMY_DATABASE_URI='sqlite:///users.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='anuragyadav2641@gmail.com',
    MAIL_PASSWORD='swkfxxcojkvxtylt',
    MAIL_DEFAULT_SENDER='anuragyadav2641@gmail.com'
)
mail = Mail(app)

OPENWEATHER_API_KEY = os.environ.get(
    'OPENWEATHER_API_KEY',
    '06c921750b9a82d8f5d1294e1586276f'
)

db.init_app(app)
CORS(app, supports_credentials=True)
login_manager = LoginManager(app)
login_manager.login_view = 'serve_index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# _______________________________________________ 
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(success=False, message='User not found.')
    if not user.check_password(password):
        return jsonify(success=False, message='Password does not match username.')
    login_user(user)
    return jsonify(success=True)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or {}
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify(success=False, message='Username already exists')
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify(success=False, message='Email already exists')
    user = User(username=data.get('username'), email=data.get('email'))
    user.set_password(data.get('password'))
    db.session.add(user)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/logout')
@login_required
def api_logout():
    logout_user()
    return jsonify(success=True)

@app.route('/api/check_auth')
def check_auth():
    return jsonify(authenticated=current_user.is_authenticated)

@app.route('/api/user_info')
@login_required
def user_info():
    return jsonify(
        username=current_user.username,
        email=current_user.email
    )

@app.route('/api/reset_password', methods=['POST'])
@login_required
def reset_password():
    data = request.json or {}
    current_pw = data.get('current_password')
    new_pw     = data.get('new_password')

    if not current_pw or not new_pw:
        return jsonify(success=False, message='Current and new passwords are required')
    if not current_user.check_password(current_pw):
        return jsonify(success=False, message='Current password does not match')
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$'
    if not re.match(pattern, new_pw):
        return jsonify(success=False,
                       message='Password must be 8+ chars, include upper, lower, digit & special')

    current_user.set_password(new_pw)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/chat_history')
@login_required
def chat_history():
    msgs = ChatMessage.query.filter_by(user_id=current_user.id) \
                             .order_by(ChatMessage.timestamp).all()
    return jsonify(history=[m.to_dict() for m in msgs])

@app.route('/api/change_username', methods=['POST'])
@login_required
def change_username():
    data = request.json or {}
    new_username = data.get('new_username', '').strip()
    if not new_username:
        return jsonify(success=False, message='Username cannot be empty')
    if User.query.filter_by(username=new_username).first():
        return jsonify(success=False, message='Username already taken')
    current_user.username = new_username
    db.session.commit()
    return jsonify(success=True, username=new_username)

@app.route('/api/change_email', methods=['POST'])
@login_required
def change_email():
    data = request.json or {}
    new_email = data.get('new_email', '').strip()
    if not new_email:
        return jsonify(success=False, message='Email cannot be empty')
    if User.query.filter_by(email=new_email).first():
        return jsonify(success=False, message='Email already in use')
    current_user.email = new_email
    db.session.commit()
    return jsonify(success=True, email=new_email)

@app.route('/api/clear_history', methods=['POST'])
@login_required
def clear_history():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify(success=True)
#__________________________________________________________________________________
@app.route('/contact', methods=['POST'])
def contact():
    name    = request.form.get('name')
    email   = request.form.get('email')
    phone   = request.form.get('phone')
    subject = request.form.get('subject')
    message = request.form.get('message')

    if not (name and email and message):
        return jsonify({"status": "error", "error": "Missing required fields"}), 400

    body = (
        f"Name:    {name}\n"
        f"Email:   {email}\n"
        f"Phone:   {phone or 'N/A'}\n"
        f"Subject: {subject or 'N/A'}\n\n"
        f"Message:\n{message}"
    )

    msg = Message(
        subject=f"New Expert Inquiry {subject or 'No Subject'}",
        recipients=["anuragyadav2641@gmail.com"],
        body=body
    )

    try:
        with mail.connect() as conn:
            conn.send(msg)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ─── NLP & ML_________________________________________________________-
nlp_processor   = AgricultureNLP()
rain_predictor  = RainPredictor('rainfall_data.csv')
crop_predictor  = CropPredictor('crop_data.csv')

@app.route('/chat', methods=['POST'])
@login_required
def handle_chat():
    msg = request.json.get('message', '')

# Future Rain forecast via NLP____
    rain_query = re.search(r'will it rain in ([\w\s]+) tomorrow', msg, re.I)
    if rain_query:
        city = rain_query.group(1).strip()
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        resp = requests.get(forecast_url)
        if resp.status_code == 200:
            data = resp.json().get('list', [])
            target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            entry = next(
                (e for e in data if e['dt_txt'].startswith(target_date) and '12:00:00' in e['dt_txt']),
                None
            )
            if entry:
                prob = entry.get('pop', 0) * 100
                desc = entry['weather'][0]['description']
                response = (
                    f"In {city.title()} next few days, "
                    f"{prob:.0f}% chance of rain: {desc}."
                )
            else:
                response = f"Sorry, no forecast entry found for {city.title()} at midday tomorrow."
        else:
            response = f"Could not fetch forecast for {city.title()}."
        return jsonify(response=response)

#  ./city weather updated final
    if msg.startswith('./'):
        city = msg[2:].strip()
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        resp = requests.get(weather_url)
        if resp.status_code == 200:
            data     = resp.json()
            cond     = data['weather'][0]['main']
            temp     = data['main']['temp']
            temp_min = data['main']['temp_min']
            temp_max = data['main']['temp_max']
            hum      = data['main']['humidity']
            wind_spd = data['wind']['speed']
            sunrise  = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%I:%M %p')
            sunset   = datetime.fromtimestamp(data['sys']['sunset']).strftime('%I:%M %p')
            response = (
                f"Weather in {city.title()}:\n"
                f"- Condition: {cond}\n"
                f"- Temperature: {temp:.1f}°C (Min: {temp_min:.1f}°C, Max: {temp_max:.1f}°C)\n"
                f"- Humidity: {hum}%\n"
                f"- Wind Speed: {wind_spd} m/s\n"
                f"- Sunrise: {sunrise}, Sunset: {sunset}"
            )
        else:
            response = f"Sorry, couldn't fetch weather for {city.title()}."
        return jsonify(response=response)

# Main chat intent logic_____________________
    analysis = nlp_processor.extract_keywords(msg)
    db.session.add(ChatMessage(user_id=current_user.id, message=msg, is_bot=False))

    if analysis['casual_intent']:
        response = handle_casual_conversation(analysis['casual_intent'])

    elif analysis['intent'] == 'weather_forecast':
        city = analysis.get('location')
        if city:
            forecast_url = (
                f"https://api.openweathermap.org/data/2.5/forecast"
                f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
            )
            resp = requests.get(forecast_url)
            if resp.status_code == 200:
                data = resp.json().get('list', [])
                target_day = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                entry = next(
                    (e for e in data if e['dt_txt'].startswith(target_day) and '12:00:00' in e['dt_txt']),
                    None
                )
                if entry:
                    prob = entry.get('pop', 0) * 100
                    desc = entry['weather'][0]['description']
                    response = f"In {city.title()} next few days, {prob:.0f}% chance of rain: {desc}."
                else:
                    response = f"Couldn't find tomorrow's forecast for {city.title()}."
            else:
                response = f"Could not fetch forecast for {city.title()}."
        else:
            response = "Please specify a city for the weather forecast."

    elif analysis['intent'] == 'crop':
        loc = analysis.get('location')

        if not loc:
            m = re.search(r'in\s+([\w\s]+?)\?*$', msg, re.I)
            if m:
                loc = m.group(1).strip()

        if loc:
            crops = crop_predictor.get_suitable_crops(loc)
            if crops:
                response = format_crop_response(crops)
            else:
                response = f"Sorry, I don't have crop data for “{loc.title()}.”"
        else:
            available = ", ".join(
                sorted(crop_predictor.data['region'].str.title().unique())
            )
            response = (
                "Please specify a region. "
                f"Available regions: {available}"
            )

    elif analysis['intent'] == 'rain':
        if analysis.get('location'):
            data = (rain_predictor.predict_future_rainfall(analysis['location'])
                    if 'future' in analysis['keywords']
                    else rain_predictor.get_average_rainfall(analysis['location']))
            response = format_rain_response(data, is_prediction='future' in analysis['keywords'])
        else:
            available = ", ".join(sorted(rain_predictor.data['Region'].unique()))
            response = f"Please specify a region. Available regions: {available}"

    else:
        response = "Sorry, I didn't understand that. Could you rephrase?"

    db.session.add(ChatMessage(user_id=current_user.id, message=response, is_bot=True))
    db.session.commit()
    return jsonify(response=response)


# Helpers
def handle_casual_conversation(intent_type):
    import random
    responses = {
        'greetings': ["Hello! I'm AgroChat. How can I help you?", "Hi there!"],
        'how_are_you': ["I'm doing great, thanks for asking!"],
        'about_bot': ["I'm AgroChat, an AI assistant for farmers."],
        'thanks': ["You're welcome!", "No problem!"],
        'where are you from':['I live in cloud', 'I do not have any physical address, I live in the cloud']
    }
    return random.choice(responses.get(intent_type, [""]))


def format_rain_response(data, is_prediction=False):
    if not data:
        return "Sorry, I couldn't find rainfall data for that region."
    if is_prediction:
        return (
            f"Predicted rainfall for {data['month']} in {data['region']}: "
            f"{data['predicted_rainfall']}mm (confidence: {data['confidence']})"
        )
    return f"Average rainfall in {data['region']}: {data['average_rainfall']}mm"


def format_crop_response(crops_data):
    items = crops_data.get('recommended_crops', [])
    if not items:
        return "Sorry, I couldn't find crop data for that region."

    region         = crops_data.get('region', 'the specified region')
    suggested      = crops_data.get('suggested', False)
    original_query = crops_data.get('original_query')

    if suggested and original_query:
        resp = (
            f"No exact crop data found for “{original_query.title()}.”\n"
            f"Showing results for the closest match: {region}\n"
        )
    else:
        resp = f"Crops commonly grown in {region}:\n"

    for c in items:
        resp += (
            f"- {c['crop']} (Season: {c['season']}, Soil: {c['soil_type']})\n"
        )

    return resp

if __name__ == '__main__':
    app.run(port=5000, debug=True)
