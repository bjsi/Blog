import logging
import os

# flask
from flask import current_app as app


@app.before_first_request
def before_first_request():
    log_level = logging.INFO
    dir = os.path.dirname(os.path.abspath(__file__))
    logdir = os.path.join(os.path.dirname(dir), 'logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    log_file = os.path.join(logdir, 'app.log')
    handler = logging.FileHandler(log_file)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)