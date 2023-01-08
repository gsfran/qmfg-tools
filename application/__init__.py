from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testDB.db'
# implement a hash key pls
app.config['SECRET_KEY'] = 'andaksfhgfsdghmsDFGDFGMSDGFHmnsgfnmafdgmsdfbs'

db = SQLAlchemy(app)

from application import routes
from application.machines import iTrak