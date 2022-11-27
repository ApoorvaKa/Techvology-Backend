from flask import Flask

from flask_cors import CORS

app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

from app import action_db, daily_tips