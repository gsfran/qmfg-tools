import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shh_its_a_secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///test_database.db'