import html
from flask import current_app as app, make_response, url_for
from flask import render_template, request, g
from werkzeug.utils import redirect
from app.comment_forms import CommentForm
from app.models import Article, User, Comment, Concept, Category, AsReplyTo
from flask import current_app
from app.search_form import SearchForm
# TODO: RSS / ATOM Feeds
#from feedgen.feed import FeedGenerator
from app.models import graph


@app.before_request
def before_request():
    g.search_form = SearchForm()


# TODO: What if concept does not exist
@app.route('/concepts/<name>/popup')
def concept_popup(name):
    """ Bootstrap popover content for concepts.
    """
    concept = Concept.get_concept(html.unescape(name))
    if concept:
        return render_template('concepts/concept_popup.html', concept=concept)


# TODO: What if article does not exist
@app.route('/article/<slug>/popup')
def summary(slug):
    """ Bootstrap popover content for Article links.
    """
    article = Article.match(graph).where(f"_.slug = \'{slug}\'").first()
    return render_template('article/article_popup.html', article=article)


@app.route("/concepts/<concept>")
def concepts(concept):
    """ Get articles matching concept.
    """
    if not Concept.exists(concept):
        return render_template('errors/404.html')
    page = request.args.get('page', 0, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)
    articles = Article.paginate_by_concept(concept=concept,
                                           endpoint="concepts",
                                           page=page,
                                           per_page=per_page)
    return render_template('search/search_results.html',
                           title=f"<span class='concept'>{concept}</span>:",
                           articles=articles.data,
                           next_url=articles.links.next_page,
                           prev_url=articles.links.prev_page,
                           page=page)


@app.route("/categories/<category>")
def categories(category):
    """ Get articles matching category.
    """
    page = request.args.get('page', 0, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)
    articles = Article.paginate_by_category(category=category,
                                            endpoint="categories",
                                            page=page,
                                            per_page=per_page)
    return render_template('search/search.html',
                           title=category,
                           articles=articles.data,
                           next_url=articles.links.next_page,
                           prev_url=articles.links.prev_page,
                           page=page)


@app.route('/search')
def search():
    if g.search_form.validate():
        page = request.args.get('page', 0, type=int)
        per_page = min(request.args.get('per_page', 5, type=int), 100)
        q = request.args.get('q', type=str)
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

# TODO: From: https://www.reddit.com/r/flask/comments/evjcc5/question_on_how_to_generate_a_rss_feed/
# @app.route('/rss')
# def rss():
#     fg = FeedGenerator()
#     fg.title('Feed title')
#     fg.description('Feed description')
#     fg.link(href='https://awesome.com')
#
#     for article in get_news(): # get_news() returns a list of articles from somewhere
#         fe = fg.add_entry()
#         fe.title(article.title)
#         fe.link(href=article.url)
#         fe.description(article.content)
#         fe.guid(article.id, permalink=False) # Or: fe.guid(article.url, permalink=True)
#         fe.author(name=article.author.name, email=article.author.email)
#         fe.pubDate(article.created_at)
#
#     response = make_response(fg.rss_str())
#     response.headers.set('Content-Type', 'application/rss+xml')
#
#     return response


@app.route('/')
def index():
    articles = Article.get_public()
    concepts = Concept.get_concepts()
    categories = Category.get_categories()
    return render_template('home_page/home.html',
                           articles=articles,
                           concepts=concepts,
                           categories=categories)


@app.route('/about')
def about():
    return render_template('about_page/about.html')


@app.route('/blog')
def blog():
    page = request.args.get('page', 0, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)
    articles = Article.paginate_public(endpoint="blog", page=page, per_page=per_page)
    return render_template('blog_page/blog.html',
                           articles=articles.data,
                           next_url=articles.links.next_page,
                           prev_url=articles.links.prev_page,
                           page=page)


@app.route('/articles/add', methods=['POST'])
def add_article():
    """ Used only by me to add new articles.
    """
    # Validate request
    if not request.authorization:
        return make_response("No authorization headers found.")

    if request.authorization.username != current_app.config["BASIC_AUTH_USERNAME"]:
        return make_response("Authorization failed.", 401)

    if request.authorization.password != current_app.config["BASIC_AUTH_PASSWORD"]:
        return make_response("Authorization failed.", 401)

    # Validate data
    data = request.json
    if not data:
        return make_response("No json data received", 400)

    title = data.get("title")
    if not title:
        return make_response("No title", 400)

    author = data.get("author")
    if not author:
        return make_response("No author", 400)

    content = data.get("content")
    if not content:
        return make_response("No content", 400)

    published = data.get("published")
    if not published:
        return make_response("No published field", 400)

    finished_confidence = data.get("finished_confidence")
    if not finished_confidence:
        return make_response("No finished_confidence field", 400)

    # Create article
    article = Article(title=title,
                      content=content,
                      published=published,
                      author=author,
                      finished_confidence=finished_confidence)
    if article.create():
        return make_response(f"New article {article.title} created successfully"), 201
    return make_response("Failed to create new article", 400)


@app.route('/articles/edit', methods=['POST'])
def edit_article():
    """ Used only by me to edit articles.

    request.json keys are the fields to edit, values are the new values.
    slug is the identifier for the article.
    """
    # Validate request
    if not request.authorization:
        return make_response("No authorization headers found.")

    if request.authorization.username != current_app.config["BASIC_AUTH_USERNAME"]:
        return make_response("Authorization failed.", 401)

    if request.authorization.password != current_app.config["BASIC_AUTH_PASSWORD"]:
        return make_response("Authorization failed.", 401)

    # Validate data
    data = request.json
    if not data:
        return make_response("No json data received", 400)

    content = data.get("content")
    slug = data.get("slug")
    if not Article.exists(slug):
        return make_response("Failed to update content because Article does not exist", 400)

    if Article.update_article(slug, data):
        return make_response("Article updated successfully", 201)
    return make_response("Failed to update Article", 400)


@app.route('/articles/<slug>', methods=['GET', 'POST'])
def detail(slug):
    form = CommentForm(request.form)

    if not Article.exists(slug):
        return render_template('errors/404.html')

    if form.validate_on_submit():
        parent = request.args.get('parent')
        username = form.username.data
        content = form.comment.data
        email = form.email.data
        user = User(username, email)
        user.register()
        comment = Comment(content)
        if parent == "article":
            comment.create(email, AsReplyTo.Article, slug)
        elif parent == "comment":
            parent_id = request.args.get('parent_id')
            comment.create(email, AsReplyTo.Comment, parent_id)
        return redirect(url_for('detail', slug=slug))

    article = Article.get_article(slug)
    return render_template('article/detailed_article_page.html',
                           article=article,
                           form=form)


@app.route('/contact')
def contact():
    return render_template('contact_page/contact.html')


