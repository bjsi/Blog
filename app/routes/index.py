# db

# Forms

# Models
from app.models.article import Article
from app.models.concept import Concept

# flask
from flask import current_app as app
from flask import render_template


@app.route('/')
def index():
    articles = Article.get_public()
    concepts = Concept.get_concepts_in_articles()
    return render_template('home_page/home.html',
                           articles=articles,
                           concepts=concepts)
