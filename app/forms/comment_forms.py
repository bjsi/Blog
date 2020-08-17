from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.usernames import banned


def username_banned(form, field):

    """ Reject invalid usernames.
    """

    if field.data in banned:
        raise ValidationError("Invalid Username")


class CommentForm(FlaskForm):

    """ Form for Users to use to post comments.
    """

    username = StringField("Display Name",
                           validators=[DataRequired(), Length(min=4, max=30), username_banned],
                           render_kw={"class": "form-control"})

    email = StringField("Email",
                        validators=[DataRequired(), Email(), Length(min=6, max=120)],
                        render_kw={"class": "form-control", "placeholder": "example@gmail.com"})

    comment = TextAreaField("Comment",
                            validators=[DataRequired(), Length(max=2500)],
                            render_kw={'cols': 32, 'rows': 5, 'class': 'form-control'})

    captcha = RecaptchaField()

    submit = SubmitField("Submit",
                         render_kw={"class": "btn btn-sm btn-outline-primary"})
