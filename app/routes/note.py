# Models
from typing import Dict

from app.models.note import Note

# flask
from flask import render_template, request
from flask import current_app as app


@app.route("/notes", methods=["GET", "POST"])
def notes():
    if request.method == "POST":
        return handle_note_post_request()
    else:
        return handle_note_get_request()


def handle_note_post_request():

    """
    Handle notes post request
    :return:
    """

    # TODO: Validation

    data = request.json
    if not data:
        return {"Message": "Failed. No data posted."}, 400

    if not validate_data(data):
        return {"Message": "Failed. Invalid data."}, 400

    title = data["title"]
    content = data["content"]

    # Update
    if Note.exists(title):
        Note.update_note(title, content)
        return Note.get_note(title), 201

    # Create
    else:
        l = Note(**data)
        if l.create():
            return l.to_dict(), 201
        else:
            return {"Message": f"Failed. Attempt to add link {title} to graph failed."}, 400


def handle_note_get_request():

    """ Return notes
    :return:
    """

    notes = Note.get_public()
    return render_template('notes_page/notes.html', notes=notes)


def validate_data(data: Dict) -> bool:

    """
    Validata link data
    :param data:
    :return:
    """

    if data.get("title") is None:
        return False
    elif data.get("content") is None:
        return False

    return True
