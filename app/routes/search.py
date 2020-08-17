from py2neo import ClientError

from app.forms.search_form import SearchForm

# Models
from app.models.article import Article

# flask
from flask import current_app as app
from flask import render_template, request, g


@app.before_request
def before_request():
    g.search_form = SearchForm()


@app.route('/search')
def search():
    if g.search_form.validate():
        page = request.args.get('page', 0, type=int)
        per_page = min(request.args.get('per_page', 5, type=int), 100)
        q = request.args.get('q', type=str)
        try:

            articles = Article.paginate_search(search=q,
                                               endpoint="search",
                                               page=page,
                                               per_page=per_page)
            return render_template('search/search_results.html',
                                   title=q,
                                   articles=articles.data,
                                   next_url=articles.links.next_page,
                                   prev_url=articles.links.prev_page,
                                   page=page)
        except ClientError:
            return render_template("search/no_results.html")






