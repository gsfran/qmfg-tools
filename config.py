import os
from dotenv import load_dotenv

load_dotenv('./.env')


class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = os.environ.get('SECRET_KEY', 'shh_its_a_secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', './.test/app.db')
