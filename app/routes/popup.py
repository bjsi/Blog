import html

# db
from app.models import graph

# models
from app.models.article import Article
from app.models.concept import Concept

# flask
from flask import current_app as app
from flask import render_template


@app.route('/concepts/<name>/popup')
def concept_popup(name):

    """ Bootstrap popover content for concepts.
    """

    concept = Concept.get_concept(name)
    if concept:
        return render_template('concepts/concept_popup.html', concept=concept)


@app.route('/article/<slug>/popup')
def summary_popup(slug: str):

    """ Bootstrap popover content for Article links.
    """

    article = Article.match(graph).where(f"_.slug = \'{slug}\'").first()
    if article:
        return render_template('article/article_popup.html', article=article)

