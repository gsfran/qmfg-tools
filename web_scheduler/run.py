import os
from ..web_scheduler import app


if __name__ == '__main__':
    if os.environ['DEBUG'] == 'True':
        app.run(host='127.0.0.1', port=5000, debug=True)
    else:
        app.run(host='10.15.5.95', port=5000, debug=False)
