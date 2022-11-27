import json
from app import app
from flask import request
from flask_sqlalchemy import SQLAlchemy, session

from datetime import datetime, timezone, timedelta
from flask_cors import CORS
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'
from hashlib import sha3_256

db = SQLAlchemy(app)

class task(db.types.UserDefinedType):
    title = db.Column(db.String(100), nullable=False)
    carbon_output = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

    def __init__(self, title='', carbon_output=0):
        self.title = title
        self.carbon_output = carbon_output

    def __repr__(self):
        return f"title: {self.title}, Carbon Output: {self.carbon_output}"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer)
    actions = db.relationship('Action', backref='user', lazy=True)

    def __init__(self, username, passhash):
        self.username = username
        self.password = passhash
        self.score = 0
    
    def __repr__(self):
        return self.username

def format_user(user):
    return{
        'id': user.id,
        'username': user.username,
        'password': user.password,
        'score': user.score,
    }

def format_task(task):
    return{
        'title': task.title,
        'carbon_output': task.carbon_output,
        'created_at': task.created_at
    }

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    carbon_output = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, carbon_output):
        self.title = title
        self.carbon_output = carbon_output
        # user id from session
        self.user_id = login.session['user_id']
    
    def __repr__(self):
        return f"title: {self.title}, Carbon Output: {self.carbon_output}"

def format_action(action):
    return{
        'id': action.id,
        'title': action.title,
        'carbon_output': action.carbon_output,
        'created_at': action.created_at,
        'user_id': action.user_id
    }

@app.route('/')
def hello():
    return 'Hello World!'

# create an event in the database
@app.route('/actions', methods=['POST'])
def create_action():
    title = request.json['title']
    carbon_output = request.json['carbon_output']
    action = Action(title, carbon_output)
    db.session.add(action)
    db.session.commit()
    return format_action(action)

# get all events from the database
@app.route('/actions', methods=['GET'])
def get_actions():
    sessionuserid = db.session.query(User).first().id
    actions = Action.query.filter_by(user_id=sessionuserid).order_by(Action.id.desc()).all() 
    return {'actions': [format_action(action) for action in actions]}

# get a single event from the database
@app.route('/actions/<int:id>', methods=['GET'])
def get_action(id):
    action = Action.query.filter_by(id=id).one()
    formatted = format_action(action)
    return {"action": formatted}

# update an event in the database
@app.route('/actions/<int:id>', methods=['PUT'])
def update_action(id):
    action = Action.query.filter_by(id=id).one()
    action.title = request.json['title']
    action.carbon_output = request.json['carbon_output']
    db.session.commit()
    return {"message": "Action updated successfully"}

# delete an event from the database
@app.route('/actions/<int:id>', methods=['DELETE'])
def delete_action(id):
    action = Action.query.filter_by(id=id).one()
    db.session.delete(action)
    db.session.commit()
    return {"message": "Action deleted successfully"}

### TESTING ###
# create an event in the database for weekly average testing
# @app.route('/actions', methods=['PATCH'])
# def edit_action():
#     title = request.json['title']
#     carbon_output = request.json['carbon_output']
#     month = request.json['month']
#     day = request.json['day']
#     action = Action(title, carbon_output)
#     action.created_at = datetime(year=2022, month=month, day=day, hour=12, minute=15, second=21, tzinfo=timezone.utc)
#     db.session.add(action)
#     db.session.commit()
#     return format_action(action)

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

# get weekly averages
@app.route('/weeklyAverages', methods=['GET'])
def weekly_averages():
    sessionuserid = db.session.query(User).first().id
    actions = Action.query.filter_by(user_id=sessionuserid).order_by(Action.id.desc()).all()
    today = datetime.now()
    sun_offset = (actions[0].created_at.weekday() - 6) % 7
    sunday = actions[0].created_at - timedelta(days=sun_offset)
    weeks = abs(sunday-today).days//7 + 1

    averages = []
    index = 0
    for _ in range(weeks):
        next_sun = sunday + timedelta(days=7)
        total = 0
        not_same = True
        
        while actions[index].created_at < next_sun and index != -1 and not_same:
            if actions[index].created_at.month == next_sun.month and actions[index].created_at.day == next_sun.day:
                not_same = False
            else: 
                total += actions[index].carbon_output
                index += 1
                if index == len(actions):
                    index = -1
        
        total /= 7

        week = str(sunday.year) + '/' + str(sunday.month) + '/' + str(sunday.day)
        avg = round(total, 2)
        weekly_average = WeeklyAverage(week, avg)
        formatted = format_weekly_average(weekly_average)
        averages.append(formatted)
        sunday = next_sun

    return averages

# attempts to authenticate the user in the database
@app.route('/login/register', methods=['POST'])
def register():
    data = request.json['body']
    username = data['username']
    password = data['password']
    hashed_password = sha3_256(password.encode('utf-8')).hexdigest()
    user = User(username, hashed_password)
    db.session.add(user)
    db.session.commit()
    if user:
        return {'message': 'success'}
    else:
        return {'message': 'failure'}

# attempts to authenticate the user
@app.route('/login', methods=['POST'])
def login():
    db.session.close()
    data = request.json['body']
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user:
        passworddata = user.password
        if(password == passworddata):
            session = True
            
            db.session.add(user)
            db.session.commit()
            print(login)
            return {'message': 'success', 'loginSuccess': True}
        #verify password
        if sha3_256(password.encode('utf-8')).hexdigest() == user.password:
            session=True
            
            db.session.add(user)
            db.session.commit()
            return {'message': user.username}
    else:
        session = False
        return {'message': 'error', 'loginSuccess': False}