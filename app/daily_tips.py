import functools
from app import app
from flask import request
from flask_sqlalchemy import SQLAlchemy
import random

from flask_cors import CORS
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass4now@localhost/techvology'

tips_path = "app/daily_tips.csv"
db = SQLAlchemy(app)

class DailyTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)

    def __init__(self, title, description):
        self.title = title
        self.description = description
    
    def __repr__(self):
        return f"title: {self.title}, description: {self.description}"

def format_daily_tip(daily_tip):
    return{
        'id': daily_tip.id,
        'title': daily_tip.title,
        'description': daily_tip.description
    }

# populate the database from `daily_tips.csv`
@app.route('/daily_tips/populate')
def populate_db():
    # clear table before repopulating the database
    DailyTip.query.delete()
    db.session.commit()
    with open(tips_path, 'r') as f:
        f.readline()
        for row in f:
            row = row.strip().split(',')
            title = row[0]
            description = row[1]
            daily_tip = DailyTip(title, description)
            db.session.add(daily_tip)
        db.session.commit()
    return "Database populated"

# get one random daily tip from the database
@app.route('/daily_tips', methods=['GET'])
def get_daily_tip():
    daily_tips = DailyTip.query.all()
    tips_list = [format_daily_tip(daily_tip) for daily_tip in daily_tips]
    random_tip = random.choice(tips_list)
    return {"daily_tip": random_tip}