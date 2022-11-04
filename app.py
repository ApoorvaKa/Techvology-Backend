from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'
db = SQLAlchemy(app)
CORS(app)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    carbon_output = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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

if __name__ == '__main__':
    app.run()