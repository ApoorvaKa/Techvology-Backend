from asyncio.windows_events import NULL
from app import app
from flask import request, session
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import ARRAY
from datetime import datetime
from flask_cors import CORS
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'
from hashlib import sha3_256

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer)
    actionLog = db.Column(ARRAY(db.Integer))
    actionDates = db.Column(ARRAY(db.String(10)))

    def __init__(self, username, passhash):
        self.username = username
        self.password = passhash
        self.score = 0
        self.actionLog = [1]
        self.actionDates = ["11/29/2022"]
    
    def __repr__(self):
        return self.username

def format_user(user):
    return{
        'id': user.id,
        'username': user.username,
        'password': user.password,
        'score': user.score,
        'actionLog': user.actionLog,
        'actionDates': user.actionDates
    }

# get all events from the database
@app.route('/user', methods=['GET'])
def get_users():
    users = User.query.order_by(User.id.desc()).all() 
    return {'users': [format_user(user) for user in users]}

# get a single user from the database
@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.filter_by(id=id).one()
    formatted = format_user(user)
    return {"user": formatted}

# get a single user from the database
@app.route('/user/<string:username>', methods=['GET'])
def get_user_username(username):
    user = User.query.filter_by(username=username).one()
    formatted = format_user(user)
    return {"user": formatted}

@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.filter_by(id=id).one()
    user.actionLog = request.json['actionLog'];
    db.session.commit()
    return {"message": "User updated successfully"}

@app.route('/userlog/<int:id>', methods=['DELETE'])
def delete_log(id):
    user = User.query.filter_by(id=id).one()
    user.actionLog = [];
    db.session.commit()
    return {"message": "Userlog deleted successfully"}

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
    data = request.json['body']
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user:
        passworddata = user.password
        if(password == passworddata):
            session = True
            print(login)

            return {'message': 'success', 'loginSuccess': True}
        #verify password
        if sha3_256(password.encode('utf-8')).hexdigest() == user.password:
            session=True
            return {'message': 'success', 'loginSuccess': True}
    else:
        session = False
        return {'message': 'error', 'loginSuccess': False}


