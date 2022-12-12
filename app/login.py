# from asyncio.windows_events import NULL
from app import app
from flask import request, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime, timezone, timedelta

from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from flask_cors import CORS
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'
from hashlib import sha3_256

from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import get_jwt_identity

import ast
import copy

app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config["JWT_SECRET_KEY"] = "secret-key-here"
app.config['SECRET_KEY'] = 'secret'
jwt = JWTManager(app)

db = SQLAlchemy(app)

uri = "postgresql://postgres:pass4now@localhost/techvology"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer)
    actionLog = db.Column(ARRAY(db.String(500)))
    #actionLog = db.Column(MutableList.as_mutable(ARRAY(db.String)))

    def __init__(self, username, passhash):
        self.username = username
        self.password = passhash
        self.score = 0
        self.actionLog = []
    
    def __repr__(self):
        repr = self.username
        for action in self.actionLog:
            repr += "\n" + str(action)

    def __append_log__(self, actionLog):
        self.actionLog.append(actionLog)

def format_user(user):
    return{
        'id': user.id,
        'username': user.username,
        'password': user.password,
        'score': user.score,
        'actionLog': user.actionLog
    }

def format_user_leaderboard(user): # only for use with leaderboard
    return{
        'id': user['id'],
        'username': user['username'],
        'score': user['score'],
    }

class UserAction():
    def __init__(self, action_id, title, carbon_output, timestamp):
        self.action_id = action_id
        self.timestamp = timestamp
        self.title = title
        self.carbon_output = carbon_output
    
    def __repr__(self):
        return f"action_id: {self.action_id}, timestamp: {self.timestamp}"

def format_user_action(user_action):
    return{
        'action_id': user_action.action_id,
        'title': user_action.title,
        'carbon_output': user_action.carbon_output,
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

# hello world with authorization TEST only
@app.route('/hello-world', methods=['GET'])
@jwt_required()
def hello_world():
    return {'message': 'Hello World'}

# get leaderboard content
@app.route('/leaderboard', methods=['GET'])
def get_leaderboard_content():
    users = User.query.order_by(User.id.desc()).all() 
    formUsers = {'users': [format_user(user) for user in users]}
    newUsers = [i for i in formUsers['users'] if not (i['score'] == 0)]
    return {'users': [format_user_leaderboard(user) for user in newUsers]}

# get user information
@app.route('/get_user', methods=['GET'])
@jwt_required()
def get_user():
    user = User.query.filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    return format_user(user)

# get users action log
@app.route('/get_log', methods=['GET'])
@jwt_required()
def get_log():
    user = User.query.filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    jsonActions = []
    for action in user.actionLog:
        jsonActions.append(ast.literal_eval(action))
    print(jsonActions)
    return jsonActions

# add an action to the logged in user's action log
@app.route('/log_action', methods=['POST'])
@jwt_required()
def add_action():
    action_id = request.json['action_id']
    title = request.json['title']
    carbon_output = request.json['carbon_output']
    timestamp = datetime.now(timezone.utc)
    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    user = db.session.query(User).filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    actions = copy.deepcopy(user.actionLog)
    newAction = UserAction(action_id, title, carbon_output, timestamp)
    formattedAction = format_user_action(newAction)
    actions.append(str(formattedAction))
    user.score = user.score + int(carbon_output)
    db.session.commit()
    user.actionLog = actions
    db.session.commit()
    return actions

# add an action to the logged in user's action log
@app.route('/log_action_week_before/<int:amount>', methods=['POST'])
@jwt_required()
def add_action_test(amount):
    action_id = request.json['action_id']
    title = request.json['title']
    carbon_output = request.json['carbon_output']
    timestamp_init = datetime.now(timezone.utc)
    timestamp = timestamp_init - timedelta(weeks = amount)
    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    user = db.session.query(User).filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    actions = copy.deepcopy(user.actionLog)
    newAction = UserAction(action_id, title, carbon_output, timestamp)
    formattedAction = format_user_action(newAction)
    actions.append(str(formattedAction))
    user.score = user.score + int(carbon_output)
    db.session.commit()
    user.actionLog = actions
    db.session.commit()
    return actions

@app.route('/del_logged_action/<int:index>', methods=['DELETE'])
@jwt_required()
def remove_action_from_log(index):
    user = db.session.query(User).filter_by(username=get_jwt_identity()).first()
    actions = copy.deepcopy(user.actionLog)
    jsonAction = ast.literal_eval(actions[index])
    carbon = jsonAction["carbon_output"]
    del actions[index]
    user.actionLog = actions
    user.score = user.score - int(carbon)
    db.session.commit()
    return "removed at " + str(index)

@app.route('/test_str_to_dict', methods=['GET'])
@jwt_required()
def load_actions_from_string():
    user = db.session.query(User).filter_by(username=get_jwt_identity()).first()
    if not user:
        return {'message': 'User not found'}
    res = ast.literal_eval(user.actionLog[0])
    return res

@app.route('/initialize_user_actions', methods=['POST'])
def clear_user_actions():
    users = User.query.order_by(User.id.desc()).all()
    print("clearing")
    for user in users:
        user.actionLog = []
    db.session.commit()
    return "Set all action logs to blank"

# ------ WEEKLY AVERAGE FUNCTIONALITY -----
class WeeklyAverage():
     def __init__(self, week, avg_carbon_output):
         self.week = week
         self.avg_carbon_output = avg_carbon_output
    
     def __repr__(self):
         return f"Week: {self.week}, Average Carbon Output: {self.avg_carbon_output}"

def format_weekly_average(weekly_average):
     return{
         'week': weekly_average.week,
         'avg_carbon_output': weekly_average.avg_carbon_output
     }

#  get weekly averages
@app.route('/weeklyAverages', methods=['GET'])
@jwt_required()
def weekly_averages():
     userActions = get_log()
     today = datetime.now()
     action_date_str = userActions[0]['timestamp']
     action_date_str = action_date_str[0:10]
     action_date_format = "%d/%m/%Y"
     action_date = datetime.strptime(action_date_str, action_date_format)
     sun_offset = (action_date.weekday() - 6) % 7
     sunday = action_date - timedelta(days=sun_offset)
     weeks = abs(sunday-today).days//7 + 1

     averages = []
     index = 0

     action_convert = []
     for idx in range(len(userActions)):
         action_date_str = userActions[idx]['timestamp']
         action_date_str = action_date_str[0:10]
         action_date_format = "%d/%m/%Y"
         action_date = datetime.strptime(action_date_str, action_date_format)
         action_convert.append(action_date)
     print(action_convert)

     for _ in range(weeks):
         next_sun = sunday + timedelta(days=7)
         total = 0
         not_same = True
        
         while action_convert[index] < next_sun and index != -1 and not_same:
             if action_convert[index].month == next_sun.month and action_convert[index].day == next_sun.day:
                 not_same = False
             else: 
                 total += int(userActions[index]['carbon_output'])
                 index += 1
                 if index == len(userActions):
                     index = -1
        
         total /= 7

         week = str(sunday.year) + '/' + str(sunday.month) + '/' + str(sunday.day)
         avg = round(total, 2)
         weekly_average = WeeklyAverage(week, avg)
         formatted = format_weekly_average(weekly_average)
         averages.append(formatted)
         sunday = next_sun

     return averages