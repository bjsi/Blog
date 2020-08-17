import logging
from enum import Enum
from . import graph
import uuid
import datetime as dt
from py2neo.ogm import GraphObject, Property
from .article import Article
from .user import User


class AsReplyTo(Enum):
    Article = 0
    Comment = 1


class Comment(GraphObject):

    """Represents a comment on an Article from a User.

    Users write comments as replies to articles: (u: User)-[:WROTE]->(c: Comment)-[:AS_REPLY_TO]->(a: Article)

    Users write comments as replies to other comments: (u: User)-[:WROTE]-(c: Comment)-[:AS_REPLY_TO]->(c: Comment)
    """

    uuid: str = Property()
    content: str = Property()
    timestamp: str = Property()

    def __init__(self, content: str) -> None:
        self.content = content
        self.timestamp = dt.datetime.now().isoformat()
        self.uuid = str(uuid.uuid4())

    def create(self, email: str, parent: AsReplyTo, parent_id) -> bool:

        """ Add a new comment.

        :param email: The commenter's email.
        :param parent: Article or Comment.
        :param parent_id: UUID or slug.
        :returns: True on success else False.
        """

        # Check user exists
        if not User.exists(email):
            logging.warning(f"Failed to create new comment because user does not exist")
            return False

        # Create comment
        graph.create(self)
        logging.debug(f"Created new comment with uuid {self.uuid}")

        # Add relationship
        base_query = """
            MERGE (u: User { email: $email })
            MERGE (c: Comment { uuid: $comment_id })
            MERGE (u)-[:WROTE]->(c)
        """

        if parent == parent.Article:
            if not Article.exists(parent_id):
                logging.warning(f"Attempted to create comment as reply to non-existent article")
                return False
            query = "MERGE (a: Article {slug: $parent_id}) " + base_query + "-[:AS_REPLY_TO]->(a)"

        elif parent == parent.Comment:
            if not Comment.exists(parent_id):
                logging.warning(f"Attempted to create comment as reply to non-existent comment")
                return False
            query = "MERGE (p: Comment {uuid: $parent_id}) " + base_query + "-[:AS_REPLY_TO]->(p)"

        graph.run(query, comment_id=self.uuid, email=email, parent_id=parent_id)
        logging.debug(f"Successfully created new comment")
        return True

    @classmethod
    def exists(cls, comment_id: str) -> bool:

        """ Checks if comment exists.

        :return: True if exists else False.
        """

        query = """
            MATCH (c: Comment { uuid: $uuid })
            RETURN c
        """

        return graph.evaluate(query, uuid=comment_id) is not None
