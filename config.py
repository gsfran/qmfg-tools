import os


class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shh_its_a_secret'
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get(
            'DATABASE_URL') or f'sqlite:///{os.path.join(basedir)}/app.db'
    )
