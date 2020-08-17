# Models
from typing import Dict

from app.models.links import Link

# flask
from flask import current_app as app
from flask import render_template, request

from app.routes.authentication import authenticated


@app.route("/links", methods=["GET", "POST"])
def links():

    """
    Handle links request
    """

    if request.method == "POST":
        return handle_links_post_request()
    else:
        return handle_links_get_request()


def handle_links_get_request():

    """
    Return links page.
    :return:
    """

    l = Link.get_links()
    return render_template('links_page/links.html', links=l)


def handle_links_post_request():

    """
    Hanlde links post request
    :return:
    """

    if not authenticated():
        return {"Message": "Authorization failed"}, 401

    data = request.json
    if not data:
        return {"Message": "Failed. No data posted."}, 400

    if not validate_data(data):
        return {"Message": "Failed. Invalid data."}, 400

    title = data["title"]

    # Update
    if Link.exists(title):
        if Link.update_link(title, data):
            return Link.get_link(title), 201
        else:
            return {"Message": f"Failed. Attempt to update link failed"}, 400

    # Create
    else:
        l = Link(**data)
        if l.create():
            return l.to_dict(), 201
        else:
            return {"Message": f"Failed. Attempt to add link {title} to graph failed."}, 400


def validate_data(data: Dict) -> bool:

    """
    Validata link data
    :param data:
    :return:
    """

    if data.get("url") is None:
        return False
    elif data.get("title") is None:
        return False
    elif data.get("author") is None:
        return False
    elif data.get("content") is None:
        return False

    return True
