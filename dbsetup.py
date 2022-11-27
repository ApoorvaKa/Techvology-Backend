from app import app, action_db, daily_tips
app.app_context().push()
#action_db.db.drop_all()
action_db.db.create_all()
#login.db.create_all()
daily_tips.db.create_all()