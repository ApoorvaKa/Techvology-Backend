# from asyncio.windows_events import NULL
from app import app
from flask import request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime, timezone, timedelta

from sqlalchemy import ARRAY
from datetime import datetime
from flask_cors import CORS
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'
from hashlib import sha3_256

from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import get_jwt_identity

app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config["JWT_SECRET_KEY"] = "secret-key-here"
app.config['SECRET_KEY'] = 'secret'
jwt = JWTManager(app)

db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer)
    actionLog = db.Column(ARRAY(db.String))

    def __init__(self, username, passhash):
        self.username = username
        self.password = passhash
        self.score = 0
        self.actionLog = []
    
    def __repr__(self):
        repr = self.username
        for action in self.actionLog:
            repr += "\n" + str(action)

def format_user(user):
    return{
        'id': user.id,
        'username': user.username,
        'password': user.password,
        'score': user.score,
        'actionLog': user.actionLog
    }

class UserAction():
    def __init__(self, action_id, timestamp):
        self.action_id = action_id
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"action_id: {self.action_id}, timestamp: {self.timestamp}"

def format_user_action(user_action):
    return{
        'action_id': user_action.action_id,
        'timestamp': user_action.timestamp
    }

# register a new user
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    passhash = sha3_256(password.encode('utf-8')).hexdigest()
    user = User(username, passhash)
    db.session.add(user)
    db.session.commit()
    return {'message': 'User created'}

# login a user
@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    passhash = sha3_256(password.encode('utf-8')).hexdigest()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {'message': 'User not found'}
    if user.password != passhash:
        return {'message': 'Invalid password'}
    access_token = create_access_token(identity=username)
    return {'access_token': access_token}

# hello world with authorization test only
@app.route('/hello-world', methods=['GET'])
@jwt_required()
def hello_world():
    return {'message': 'Hello World'}

# get user information
@app.route('/get_user', methods=['GET'])
@jwt_required()
def get_user():
    user = User.query.filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    return format_user(user)

# add an action to the logged in user's action log
@app.route('/add_action', methods=['POST'])
@jwt_required()
def add_action():
    action_id = request.json['action_id']
    timestamp = datetime.now(timezone.utc)
    user = User.query.filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    newAction = UserAction(action_id, timestamp)
    formattedAction = format_user_action(newAction)
    return format_user(user)