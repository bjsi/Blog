# Forms
from app.forms.comment_forms import CommentForm

# Models
from app.models.article import Article
from app.models.user import User
from app.models.comment import Comment, AsReplyTo

# flask
from flask import current_app as app, url_for
from flask import render_template, request
from werkzeug.utils import redirect


@app.route('/comments/<slug>', methods=["POST"])
def comments(slug: str):

    """
    Handle adding comments.
    :return:
    """

    form = CommentForm(request.form)
    validated = form.validate_on_submit()

    if validated and slug is not None:

        # Get data
        parent = request.args.get('parent')
        username = form.username.data
        content = form.comment.data
        email = form.email.data

        # Register user
        user = User(username, email)
        user.register()

        comment = Comment(content)
        if parent == "article":
            comment.create(email, AsReplyTo.Article, slug)

        elif parent == "comment":
            parent_id = request.args.get('parent_id')
            comment.create(email, AsReplyTo.Comment, parent_id)

        return redirect(url_for('articles', slug=slug))

    article = Article.get_article(slug=slug)
    return render_template('article/detailed_article_page.html',
                           article=article,
                           form=form)

