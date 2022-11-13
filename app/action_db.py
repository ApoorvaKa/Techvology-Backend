import json
from app import app
from flask import request
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime, timezone, timedelta
from flask_cors import CORS
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/techvology'

db = SQLAlchemy(app)

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    carbon_output = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

    def __init__(self, title, carbon_output):
        self.title = title
        self.carbon_output = carbon_output
    
    def __repr__(self):
        return f"title: {self.title}, Carbon Output: {self.carbon_output}"

def format_action(action):
    return{
        'id': action.id,
        'title': action.title,
        'carbon_output': action.carbon_output,
        'created_at': action.created_at
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
    actions = Action.query.order_by(Action.id.asc()).all() 
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

# get weekly averages
@app.route('/weeklyAverages', methods=['GET'])
def weekly_averages():
    actions = Action.query.order_by(Action.created_at.asc()).all()
    today = datetime.now()
    sun_offset = (actions[0].created_at.weekday() - 6) % 7
    sunday = actions[0].created_at - timedelta(days=sun_offset)
    weeks = abs(sunday-today).days//7 + 1

    averages = {}
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

        key = str(sunday.year) + '/' + str(sunday.month) + '/' + str(sunday.day)
        averages[key] = round(total, 2)
        sunday = next_sun

    return json.dumps(averages)
