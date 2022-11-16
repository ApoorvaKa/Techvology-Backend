from app import app
from flask import request, session
from flask_sqlalchemy import SQLAlchemy

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
        'password': user.password
    }

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


