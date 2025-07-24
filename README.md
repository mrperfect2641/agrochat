# 🌾 AgroChat – AI-Based Agricultural Chatbot

AgroChat is a smart, AI-powered chatbot web application developed to assist farmers with region-specific agricultural support. It offers real-time weather data, crop recommendations, rainfall prediction, and allows farmers to ask questions in natural language.

---

## 🔍 Features

- 💬 **Smart Chatbot** using NLP for detecting user intent.
- 🌦️ **Live Weather Forecast** via OpenWeatherMap API.
- 🌱 **Crop Recommendation System** based on soil & climate conditions.
- 🌧️ **Rainfall Prediction** using machine learning models.
- 📈 **Future Rainfall Forecast** with data trends and predictions.
- 🔐 **User Authentication** – Secure Login & Registration.
- 🗃️ **Chat History with Filters** for tracking past queries.
- 📩 **Expert Contact Form** with Email integration (Flask-Mail).
- 📊 **Interactive Dashboard** with additional settings and visual data.

---

## 🛠️ Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, Flask
- **Database**: SQLite
- **Machine Learning**: Random Forest, Naive Bayes, Decision Tree
- **NLP**: Text processing, intent detection
- **APIs**: OpenWeatherMap API
- **Tools**: Flask-Mail, Flask-CORS, Git, VS Code

---

## 📁 Project Structure

```bash
AgroChat/
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── login.html, register.html, etc.
├── static/
│   ├── css/
│   ├── js/
├── models.py
├── main.py
├── NLP.py
├── crop_pred.py
├── rain_pred.py
├── requirements.txt
├── README.md
└── ...

How to Run Locally

Clone the repository:
git clone https://github.com/mrperfect2641/agrochat.git
cd agrochat

Create Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install Dependencies:
pip install -r requirements.txt
Run the App

python main.py
Visit: http://localhost:5000 in your browser.