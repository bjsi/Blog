from flask import current_app as app
from flask import render_template


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html')


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html')

