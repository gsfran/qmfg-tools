from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db: SQLAlchemy = SQLAlchemy(app)
migrate: Migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'  # type: ignore[call-arg]


login.login_message_category = 'warning'


@app.before_first_request
def create_tables():
    db.create_all()


from application import routes, models  # noqa
