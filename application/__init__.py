from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# implement a hash key pls
# app.config['SECRET_KEY'] = 'andaksfhgfsdghmsDFGDFGMSDGFHmnsgfnmafdgmsdfbs'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ProductionDB.db'

db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()

from application import routes
# from application.machines import iTrak