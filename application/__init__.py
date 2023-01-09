from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# implement a hash key pls
app.config['SECRET_KEY'] = 'andaksfhgfsdghmsDFGDFGMSDGFHmnsgfnmafdgmsdfbs'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testDB.db'

db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()

# with app.app_context():
#     db.create_all()

from application import routes
# from application.machines import iTrak