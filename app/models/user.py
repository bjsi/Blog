import logging
import hashlib
from flask_avatars import Identicon
from passlib.handlers import bcrypt
from py2neo import Node
from py2neo.ogm import GraphObject, Property
from app.models import graph


class User(GraphObject):
    """ Represents a commenter.

    (u: User)-[:WROTE]->(c: Comment)-[:AS_REPLY_TO]->(a: Article)

    (u: User)-[:WROTE]->(c: Comment)-[:AS_REPLY_TO]->(other: Comment)
    """
    __primarykey__ = "email"

    username: str = Property()
    email: str = Property()
    avatar: str = Property()

    def __init__(self, username: str, email: str) -> None:
        self.email = email
        # Adds part of the email hash
        self.username = username + "-" + hashlib.sha224(username.encode('utf-8')).hexdigest()[:5]
        self.avatar = self.generate_avatar()

    def register(self) -> None:
        """ Register a new user.

        Flask-wtf takes care of data validation.

        :return: Result object with status and message.
        """
        # Create new user
        user = Node('User',
                    avatar=self.avatar,
                    username=self.username,
                    email=self.email)
        graph.create(user)
        logging.debug(f"Created new user {self.username}")

    def generate_avatar(self) -> str:
        """ Generate an avatar based on the username.

        :return: Filepath of the avatar.
        """
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        avatar = filenames[0]
        logging.debug(f"Generated avatar with fp {avatar} for {self.username}")
        return avatar

    @classmethod
    def get_user_by_email(cls, email: str) -> "User":
        """ Find a user according to their email address.
        """
        user = User.match(graph).where(f"_.email = \'{email}\'")
        return user

    @classmethod
    def verify_password(cls, email: str, password: str) -> False:
        """ Verify password is the user's password.

        :return: True if password is the registered user's password else False.
        """
        user = User.get_user_by_email(email)
        if user:
            return bcrypt.verify(password, user.password)
        return False

    @classmethod
    def exists(cls, email: str) -> bool:
        """ Check if username exists.

        :returns: True if exists else False.
        """
        query = """
            MATCH (u: User { email: $email })
            RETURN u
        """
        return (email is not None) and (graph.evaluate(query, email=email) is not None)
