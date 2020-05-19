from flask import Flask


def create_app():
    """ Application Factory Style """

    app = Flask(__name__)

    with app.app_context():
        from . import models
        from . import views

        return app