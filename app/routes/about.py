# flask
from flask import current_app as app
from flask import render_template


@app.route('/about')
def about():

    """
    Return the about page
    :return:
    """

    return render_template('about_page/about.html')

