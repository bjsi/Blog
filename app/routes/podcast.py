# Models
from app.models.podcast import Podcast

# flask
from flask import current_app as app
from flask import render_template


@app.route("/podcasts")
def podcast():

    """
    Return podcasts page.
    :return:
    """

    p = Podcast.get_public()
    return render_template("podcast/podcasts.html", podcasts=p)

