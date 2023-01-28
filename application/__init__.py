from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()

from application import routes
# from application.machines import iTrak