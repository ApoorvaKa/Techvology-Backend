from flask import Flask

from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'
CORS(app)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

from app import login, action_db, daily_tips