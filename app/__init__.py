from flask import Flask
from config import Config
from flask_log import Logging


def create_app():
    """ Application Factory Style """

    app = Flask(__name__)
    app.config.from_object(Config)
    flask_log = Logging(app)

    with app.app_context():

        from . import models
        from . import views
        from . import errors

        return app