from flask import Flask
from config import Config


def create_app():

    """ Application Factory
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():

        from . import models

        # Routes
        from app.routes import logging
        from app.routes import about
        from app.routes import blog
        from app.routes import comment
        from app.routes import concept
        from app.routes import errors
        from app.routes import index
        from app.routes import links
        from app.routes import note
        from app.routes import podcast
        from app.routes import popup
        from app.routes import rss
        from app.routes import search

        return app