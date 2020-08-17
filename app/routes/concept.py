from typing import Dict
from itertools import groupby
from app.models.article import Article
from app.models.concept import Concept

# flask
from flask import current_app as app, logging
from flask import render_template, request


#@app.route("/concepts", methods=["GET", "POST"])
#def concept():
#
#    """
#    Handle requests for concepts
#    """
#
#    c = Concept.get_concepts()
#    return render_template("concepts/concepts.html", concepts=c)


@app.route("/concepts", methods=["GET", "POST"])
def concepts():

    """
    Handle requests for concepts.
    :param concept: Name of the concept.
    :return:
    """

    if request.method == "POST":
        return handle_concept_post_request()
    else:
        return handle_concept_get_request()


def handle_concept_post_request():

    """
    Handle post requests for concepts.
    :param concept:
    :return:
    """

    # TODO: Validation

    data = request.json
    if not data:
        return {"Message": "Failed. No data posted."}, 400

    name = data["name"]
    content = data["content"]

    if not validate_data(data):
        return {"Message": "Failed. Invalid data."}, 400

    if Concept.exists(name):
        if Concept.update_concept(name, content):
            return Concept.get_concept(name), 201
        else:
            return {"Message": f"Failed. Attempt to update concept {name} failed."}, 400

    else:
        l = Concept(**data)
        if l.create():
            return l.to_dict(), 201
        else:
            return {"Message": f"Failed. Attempt to add concept {name} to graph failed."}, 400


def validate_data(data: Dict) -> bool:

    """
    Validata concept data
    :param data:
    :return:
    """

    if data.get("name") is None:
        return False
    elif data.get("content") is None:
        return False

    return True


def handle_concept_get_request():

    """
    Handle get requests for concepts.
    :param concept:
    :return:
    """

    concept = request.args.get("concept")
    if concept:

        page = request.args.get('page', 0, type=int)
        per_page = min(request.args.get('per_page', 5, type=int), 100)
        articles = Article.paginate_by_concept(concept=concept, endpoint="concepts", page=page, per_page=per_page)

        return render_template('search/search_results.html',
                               title=f"<span name='{concept}' class='concept'>{concept}</span>:",
                               articles=articles.data,
                               next_url=articles.links.next_page,
                               prev_url=articles.links.prev_page,
                               page=page)
    else:
        concepts = Concept.get_all_concepts_with_linked()
        groups = groupby(concepts, lambda x: x["name"][0])
        grouped_concepts = [
            (group[0], list(group[1]))
            for group in groups
        ]

        for group in grouped_concepts:
            group[1].sort(key=lambda x: x["name"])

        return render_template("concepts/concepts.html", grouped_concepts=grouped_concepts)


