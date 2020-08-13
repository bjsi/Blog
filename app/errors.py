from flask import render_template
from flask import current_app as app


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html')


@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html')

