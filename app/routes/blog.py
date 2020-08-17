from typing import Dict

from app.forms.comment_forms import CommentForm
from app.models.article import Article

# flask
from flask import current_app as app, make_response, url_for
from flask import render_template, request, g


@app.route("/articles/<slug>", methods=["GET"])
def article(slug: str):

    form = CommentForm(request.form)
    article = Article.get_article(slug=slug)
    return render_template('article/detailed_article_page.html',
                           article=article,
                           form=form)


@app.route('/articles', methods=["GET", "POST"])
def articles():

    """
    Handle requests for articles.
    :return:
    """

    if request.method == "POST":
        return handle_articles_post_request()
    else:
        return handle_articles_get_request()


def handle_articles_get_request():

    """
    Handle GET requests for articles
    :return:
    """

    page = request.args.get('page', 0, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)
    articles = Article.paginate_public(endpoint="articles", page=page, per_page=per_page)
    return render_template('blog_page/blog.html',
                           articles=articles.data,
                           next_url=articles.links.next_page,
                           prev_url=articles.links.prev_page,
                           page=page)


def handle_articles_post_request():

    """
    Handle articles POST request.
    :return:
    """

    # Validate request
    #if not request.authorization:
    #    return make_response("No authorization headers found.")

    #if request.authorization.username != app.config["BASIC_AUTH_USERNAME"]:
    #    return make_response("Authorization failed.", 401)

    #if request.authorization.password != app.config["BASIC_AUTH_PASSWORD"]:
    #    return make_response("Authorization failed.", 401)

    data = request.json
    if not data:
        return {"Message": "Failed. No data posted."}, 400

    if not validate_data(data):
        return {"Message": "Failed. Invalid data."}, 400

    title = data["title"]

    # Update
    if Article.exists(title):
        if Article.update_article(title, data):
            # TODO: return dict
            return {"Message": "Successfully updated article"}, 201
        else:
            return {"Message": f"Failed. Attempt to add link {title} to graph failed."}, 400

    # Create
    else:
        article = Article(**data)
        if article.create():
            return article.to_dict(), 201
        else:
            return {"Message": f"Failed. Attempt to add link {title} to graph failed."}, 400


def validate_data(data: Dict) -> bool:

    """
    Validate posted data.
    :param data:
    :return:
    """

    if not data.get("title"):
        return False
    if not data.get("author"):
        return False
    if not data.get("content"):
        return False
    if not data.get("published"):
        return False
    if not data.get("finished_confidence"):
        return False

    return True

