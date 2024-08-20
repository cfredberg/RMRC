import flask

def process():
    app = flask.Flask(__name__)

    @app.route('/')
    def index():
        return flask.render_template('index.html')
    
    app.run(debug=False, port=5000, host='0.0.0.0', threaded=True, processes=1)