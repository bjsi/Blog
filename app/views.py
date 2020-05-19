from flask import current_app as app
from flask import render_template, request
from app.models import Article


@app.route('/')
def index():
    articles = (Article
                .get_public())
    return render_template('home.html', articles=articles)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/blog')
def blog():
    page = request.args.get('page', 0, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)
    articles = Article.paginate_public('blog', page, per_page)
    return render_template('blog.html',
                           articles=articles["data"],
                           next_page=articles["_links"]["next_page"],
                           prev_url=articles["_links"]["prev_page"])


@app.route('/articles/<slug>')
def detail(slug):
    article = Article.with_slug(slug)
    if article:
        return render_template('article.html', article=article)
    return render_template('404.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')