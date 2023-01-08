from application import app


@app.route('/')
def index():
    return App.render(render_template('index.html'))