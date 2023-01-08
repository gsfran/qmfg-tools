import os
import jyserver.Flask as jsf
from flask import Flask, render_template


app = Flask(__name__)

@jsf.use(app)
class App:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1
        self.js.document.getElementById('count').innerHTML = self.count

@app.route('/')
def index():
    return App.render(render_template('index.html'))


if __name__ == '__main__':
    
    app.run(host='127.0.0.1', port=8080, debug=True)