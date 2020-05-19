from typing import List, NamedTuple, Tuple
from flask import url_for
from py2neo import Graph, Node, Relationship
from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
import datetime as dt
import os
from passlib.hash import bcrypt
import uuid
from slugify import slugify


password = os.getenv('NEO4J_PASSWORD')
username = os.getenv("NEO4J_USERNAME")
graph = Graph(username=username, password=password)


# TODO: Use unique constraints?
# graph.schema.create_uniqueness_constraint("User", "username")
# graph.schema.create_uniqueness_constraint("Tag", "name")
# graph.schema.create_uniqueness_constraint("Post", "id")


class ConceptMention:

    name: str
    mentions: List[int]

    def __init__(self, name: str, mentions: List[int]):
        self.name = name
        self.mentions = mentions

    def to_dict(self):
        return {
            self.name: self.mentions
        }


class Comment(GraphObject):
    """
    Represents a comment on an Article from a User.
    (c: Comment)<-[:HAS_COMMENT]-(a: Article)
    (c: Comment)<-[:WROTE_COMMENT]-(u: User)
    (c: Comment)-[:AS_REPLY_TO]->(c: Comment)
    """

    uuid: str = Property()
    content: str = Property()
    timestamp: str = Property()

    # Relationships
    article = RelatedFrom("Article", "HAS_COMMENT")
    author = RelatedFrom("User", "WROTE_COMMENT")

    # Comment thread
    parent = RelatedTo("Comment", "REPLY_TO")
    children = RelatedFrom("Comment", "REPLY_TO")

    def __init__(self, content: str):
        self.content = content
        self.timestamp = dt.datetime.now().isoformat()
        self.uuid = str(uuid.uuid4())


class Article(GraphObject):
    """
    Represents an Article I posted.
    (a: Article)<-[:ON]-(c: Comment)
    """
    __primarykey__ = "uuid"

    uuid: str = Property()
    title: str = Property()
    content: str = Property()
    published: bool = Property()
    timestamp: str = Property()
    slug: str = Property()

    # TODO: Unreliable?
    # Relationships
    concepts = RelatedTo("Concept", "HAS_CONCEPT")
    comments = RelatedTo("Comment", "HAS_COMMENT")

    def __init__(self, title: str, content: str, published: bool = False):
        self.uuid = str(uuid.uuid4())
        self.title = title
        self.content = content
        self.published = published
        self.timestamp = dt.datetime.now().isoformat()
        self.slug = slugify(title)

    def create(self, concepts: List[ConceptMention]):
        graph.merge(self)
        for concept in concepts:
            query = """
                MERGE (c: Concept {name: $name})
                MERGE (a: Article {uuid: $uuid})
                MERGE (a)-[:HAS_CONCEPT {mentions: $mentions}]->(c)
            """
            graph.run(query, name=concept.name, mentions=concept.mentions, uuid=self.uuid)

    def add_comment(self, username, comment: str, parent: None):
        query = """
            MERGE ()                    
        """
        pass

    @classmethod
    def get_public(cls):
        query = """
            MATCH (a: Article)-[:HAS_CONCEPT]->(c: Concept)
            WHERE a.published
            RETURN a, COLLECT(c.name) AS concepts
        """
        data = graph.run(query)
        return [
            {**item["a"], "concept": item["concepts"]}
            for item in data
        ]

    def get_similar_articles(self):
        """
        Find articles with overlapping tags.
        :return:
        """
        query = """
            MATCH (this: Article {uuid: $uuid})-[:HAS_CONCEPT]->(c: Concept),
                  (other: Article)-[:HAS_CONCEPT]->(c)
            WHERE this <> other
            WITH other, COLLECT(DISTINCT concept.name) as concepts
            ORDER BY SIZE(concepts) DESC LIMIT 3
            RETURN other.title as similar_article, concepts 
        """
        return graph.run(query, uuid=self.uuid)

    # TODO: Make sure slugs are unique
    @classmethod
    def with_slug(cls, slug: str):
        query = """
            MATCH (a: Article)
            OPTIONAL MATCH (a)-[:HAS_CONCEPT]->(c: Concept)
            WHERE a.published AND a.slug = $slug
            RETURN a, COLLECT(c.name) AS concepts
            LIMIT 1
        """
        data = graph.run(query, slug=slug).data()
        res = {**data[0]['a'], "concepts": data[0]["concepts"]}
        return res

    @classmethod
    def paginate_public(cls, endpoint: str, page: int = 0, per_page: int = 5):
        """
        Get all published articles ordered by most recent.
        """
        query = """
            MATCH (a: Article)-[:HAS_CONCEPT]->(c: Concept)
            WHERE a.published
            RETURN a, COLLECT(c.name) AS concepts
            ORDER BY a.timestamp DESC
            SKIP $skip
            LIMIT $limit
        """
        skip = page * per_page
        limit = per_page + 1
        data = graph.run(query, skip=skip, limit=limit).data()
        has_next = len(data) >= per_page
        if has_next:
            data = data[:-1]
        return {
            "data": [
                {**item['a'], "concepts": item["concepts"]}
                for item in data
            ]
            ,
            "_meta": {
                "current_page": page,
                "items_per_page": per_page,
            },
            "_links": {
                 "current_page": url_for(endpoint, page=page, per_page=per_page),
                 "next_page": url_for(endpoint, page=page, per_page=per_page)
                                  if has_next else None,
                 "prev_page": url_for(endpoint, page=page, per_page=per_page)
                                  if page != 0 else None
            }
        }


# TODO: Enrich the graph with concept-net or wikidata information
# TODO: Add Concept to Concept links
class Concept(GraphObject):
    """
    Represents a Concept in an Article.
    Can act like a general tag.
    Can also act as a Keyword or Noun Phrase inside the article mentioned one or more times.
    (c: Concept)<-[:HAS_CONCEPT {mentions: [{start_char: int}]-(a: Article)
    (c: Concept)<-[:HAS_CONCEPT]-(a: Article)
    """
    __primarykey__ = "name"
    name: str = Property()

    # TODO: Unreliable
    # Relationships
    articles = RelatedFrom("Article", "HAS_CONCEPT")

    def __init__(self, name):
        self.name = name


class User(GraphObject):
    """
    Represents a Commenter on an Article.
    (u: User)-[:POSTED_COMMENT]->(c: Comment)
    """
    __primarykey__ = "username"

    username: str = Property()
    password: str = Property()

    # Relationships
    comments = RelatedTo("Comment", "WROTE_COMMENT")

    def __init__(self, username: str):
        self.username = username

    def register(self, password: str) -> bool:
        """
        :param password:
        :return: True on success else False.
        """
        if not self.find():
            user = Node('User', username=self.username, password=bcrypt.hash(password))
            graph.create(user)
            return True
        return False

    def verify_password(self, password):
        """
        :param password:
        :return: True on success else False.
        """
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        return False

    @classmethod
    def find(self):
        pass
