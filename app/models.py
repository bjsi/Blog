from enum import Enum
from flask_avatars import Identicon
from typing import List, Optional, Dict, Any
import hashlib
from py2neo import Graph, Node
from py2neo.ogm import GraphObject, Property
import datetime as dt
import os
from passlib.hash import bcrypt
import uuid
from slugify import slugify
from app.BlogArticle import BlogArticle
from app.category_parser import get_categories, remove_categories
from app.comments import clean_comments_recursive, ArticleComments
from app.concept_parser import ConceptNet
from app.concept_parser import parse_concepts
from app.pagination import Paginated
from app.summary_parser import parse_summary
import logging

password = os.getenv('NEO4J_PASSWORD')
user = os.getenv("NEO4J_USERNAME")
# graph = Graph(user=user, password=password)
graph = Graph("BlogTest", password="helloworld")


def add_fts_index():
    query = """
         CALL db.index.fulltext.createNodeIndex("articleContent",["Article"],["title",
                                                                              "content",
                                                                              "author",
                                                                              "timestamp",
                                                                              "summary"])
    """
    graph.run(query)


def drop_fts_index():
    query = """
    """
    pass


# Query
# CALL db.index.fulltext.queryNodes("articleContent", "query") YIELD node, score
# RETURN node.title, node.description, score

# graph.schema.create_uniqueness_constraint("User", "username")
# graph.schema.create_uniqueness_constraint("Article", "uuid")
# graph.schema.create_uniqueness_constraint("Comment", "uuid")
# graph.schema.create_uniqueness_constraint("Concept", "name")


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

        :param username: Username.
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


class Article(GraphObject):
    """ Represents an Article.

    (User)-[:WROTE]-(Comment)-[:AS_REPLY_TO]->(Article)

    (Article)-[:HAS_CONCEPT]->(Concept)

    (Article)-[:HAS_CATEGORY]->(Category)
    """
    __primarykey__ = "uuid"

    uuid: str = Property()
    summary: str = Property()
    title: str = Property()
    author: str = Property()
    content: str = Property()
    published: bool = Property()
    timestamp: str = Property()
    last_edited: str = Property()
    finished_confidence: int = Property()
    slug: str = Property()

    def __init__(self,
                 title: str,
                 content: str,
                 finished_confidence: int,
                 published: bool = False,
                 author: str = "Jamesb"):

        self.uuid = str(uuid.uuid4())
        self.title = title
        self.content = content
        self.published = published
        self.author = author
        self.finished_confidence = finished_confidence
        self.timestamp = dt.datetime.now().isoformat()
        self.last_edited = self.timestamp
        self.slug = slugify(title)

    @classmethod
    def add_concepts(cls, slug: str) -> None:
        """ Add concept relations to the Article.
        """
        if not Article.exists(slug):
            logging.warning(f"Failed to add concepts because Article does not exist")
            return

        article = Article.match(graph).where(f"_.slug = \'{slug}\'").first()

        # Add concept net concepts
        concepts = parse_concepts(article.content)
        if not concepts:
            return

        # cn = ConceptNet()
        # concepts = cn.add_related_concepts(concepts)

        # Add concept relations to graph
        for concept in concepts:
            # Add concept
            query = """
                MERGE (c: Concept { name: $name })
                MERGE (a: Article { uuid: $uuid })
                MERGE (a)-[:HAS_CONCEPT { mentions: $mentions }]->(c)
            """
            graph.run(query, name=concept.name, mentions=concept.mentions, uuid=article.uuid)
            logging.debug(f"Added Article-Concept relationship between {article.slug} and {concept.name}")

            # Add related concepts
            for related in concept.related:
                query = """
                    MERGE (fst: Concept { name: $fst_name })
                    MERGE (snd: Concept { name: $snd_name })
                    MERGE (fst)-[:RELATED_TO { weight: $weight }]-(snd)
                """
                graph.run(query,
                          fst_name=concept.name,
                          snd_name=related.name,
                          weight=related.weight)
                logging.debug(f"Added Concept-Concept relationship with weight {related.weight} between concepts {concept.name} and {related.name}")

    @classmethod
    def add_categories(cls, slug: str, categories: List[str]) -> None:

        """ Add categories to the Article
        """

        if not Article.exists(slug):
            logging.warning(f"Failed to add categories to Article because it does not exist")
            return

        article = Article.match(graph).where(f"_.slug = \'{slug}\'").first()

        for category in categories:
            query = """
                MERGE (c: Category { name: $name })
                MERGE (a: Article { uuid: $uuid })
                MERGE (a)-[:HAS_CATEGORY]->(c)
            """
            graph.run(query, name=category, uuid=article.uuid)
            logging.debug(f"Added category {category} to {article.slug}")

    def create(self) -> bool:

        """ Create an Article and add concept relations.

        :returns: True on success else False.
        """

        # Check uniqueness
        if Article.exists(self.slug):
            logging.warning(f"Failed to create new article \'{self.slug}\' because an article with that slug already exists.")
            return False

        # Get summary information
        self.summary = parse_summary(self.content)

        # Get category information
        categories = get_categories(self.content)
        self.content = remove_categories(self.content)

        # Create article
        graph.merge(self)
        logging.debug(f"Created new Article {self.slug}")

        # Add relationships
        Article.add_categories(self.slug, categories)
        Article.add_concepts(self.slug)

        return True

    # TODO: Ignoring Title / Slug for simplicity: If Title updated, re-slugify
    # actually don't re slugify - would break people's links
    @classmethod
    def update_article(cls, slug: str, update_info: Dict[str, Any]) -> bool:
        """ Update an article's properties.

        Ignores slug.
        Ignores new properties.

        :return: True on success else False.
        """
        if not Article.exists(slug):
            logging.warning(f"Failed to update content because article with slug {slug} does not exist")
            return False

        if not update_info:
            logging.warning(f"Called update_article with empty update_info")
            return False

        article_fields = list(vars(Article)["__annotations__"].keys())
        for key, value in update_info.items():
            # Don't allow adding new properties
            if key not in article_fields:
                logging.warning(f"Attempted to add new field to Article")
                continue
            elif key == "content":
                Article.__update_content(slug, value)
            elif key == "slug" or key == "title":
                continue
            else:
                Article.__update_property(slug, value)
        return True

    @classmethod
    def __update_property(cls, slug: str, key: str, value: Any) -> bool:
        """
        :param slug: Article slug.
        :param value: New value.
        :return: True on success else False.
        """
        if not Article.exists(slug):
            logging.warning(f"Failed to update property because article with slug {slug} does not exist")
            return False

        article_fields = list(vars(Article)["__annotations__"].keys())
        if key not in article_fields:
            logging.warning(f"Attempted to add new field to Article")
            return False
        elif key == "content":
            logging.warning(f"Attempted to update content field - use update_content method instead")
            return False

        query = f"""
            MATCH (a: Article)
            WHERE a.slug = $slug
            SET a.{key} = $value
        """
        graph.run(query, slug=slug, value=value)
        logging.debug(f"Updated {key} field of {slug} to {value}")
        return True

    @classmethod
    def __update_content(cls, slug, value) -> bool:
        """ Update the content of an existing article.

        :param slug: Article slug.
        :param value: New article content.
        :return: True on success else False.
        """
        if not Article.exists(slug):
            logging.warning(f"Failed to update content because article with slug {slug} does not exist")
            return False
        try:

            # Get categories and summary
            categories = get_categories(value)
            content = remove_categories(value)
            summary = parse_summary(value)

            tx = graph.begin()
            # 1. Delete concept relationships
            query = """
                MATCH (Concept)<-[rel:HAS_CONCEPT]-(Article { slug: $slug })
                DELETE rel
            """
            graph.run(query, slug=slug)

            # 2. Delete category relationships
            query = """
                MATCH (Category)<-[rel:HAS_CATEGORY]-(Article { slug: $slug })
                DELETE rel
            """
            graph.run(query, slug=slug)

            # 3. Update content and last_edited
            query = """
                MATCH (a: Article { slug: $slug })
                SET a.content = $content
                SET a.last_edited = $last_edited
                SET a.summary = $summary
            """
            last_edited = dt.datetime.now().isoformat()
            graph.run(query, content=content, summary=summary, last_edited=last_edited, slug=slug)
            tx.commit()
            logging.debug(f"Updated content for Article {slug}")

            # 3. Update concept relationships
            Article.add_categories(slug, categories)
            Article.add_concepts(slug)
            return True

        except Exception as e:
            logging.error(f"Failed to update content with exception {e}")
            return False

    @classmethod
    def exists(cls, slug: str) -> bool:
        """ Checks if an Article exists.

        :return: True if exists else False.
        """
        query = """
            MATCH (a: Article { slug: $slug })
            RETURN a
        """
        return graph.evaluate(query, slug=slug) is not None

    # TODO: Test
    @classmethod
    def get_public(cls) -> List:
        """ Get all published Articles.

        :return: A List representing all published Articles.
        """
        query = """
            MATCH (article: Article { published: True })
            OPTIONAL MATCH (article: Article {published: True})-[rel:HAS_CONCEPT]->(concept: Concept)
            OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
            RETURN article{.*, concepts: concepts, categories: categories }
        """
        data = graph.run(query).data()
        if not data:
            return []
        return [
            item["article"]
            for item in data
        ]

    # TODO: Test
    @classmethod
    def get_private(cls) -> List:
        """ Get all unpublished Articles.

        :return: A List representing all unpublished Articles.
        """
        query = """
            MATCH (article: Article { published: False })
            OPTIONAL MATCH (article: Article {published: False})-[rel:HAS_CONCEPT]->(concept: Concept)
            OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
            RETURN article{.*, concepts: concepts, categories: categories }
        """
        data = graph.run(query).data()
        if not data:
            return []
        return [
            item["article"]
            for item in data
        ]

    # TODO: Test
    # TODO: Add categories?
    @classmethod
    def get_similar_articles(cls, slug) -> List:
        """ Find articles with overlapping tags.

        :return: List or None
        """
        # Check existence
        if not Article.exists(slug):
            logging.warning(f"Failed to get similar articles because article with slug {slug} does not exist")
            return []

        # Find similar articles
        query = """
            MATCH (this: Article { slug: $slug })-[:HAS_CONCEPT]->(c: Concept),
                  (other: Article)-[rel:HAS_CONCEPT]->(c)
            WHERE this <> other
            WITH DISTINCT c as c, other, rel
            WITH other, COLLECT(rel{.*, name: c.name}) as concepts
            ORDER BY SIZE(concepts) DESC LIMIT 3
            RETURN other{.*, concepts: concepts}
        """
        data = graph.run(query, slug=slug).data()
        if not data:
            return []
        return [
            item["article"]
            for item in data
        ]

    # TODO: Need to check if public?
    # TODO: Test
    @classmethod
    def get_article(cls, slug: str) -> Optional[BlogArticle]:
        """ Get Article by slug name.

        :return: BlogArticle or None.
        """
        if not Article.exists(slug):
            return None

        query = """
            MATCH (article: Article { slug: $slug })
            OPTIONAL MATCH (article: Article {slug: $slug})-[rel:HAS_CONCEPT]->(concept: Concept)
            OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
            RETURN article{.*, concepts: concepts, categories: categories }
        """
        data = graph.run(query, slug=slug).data()
        if not data:
            logging.error(f"get_article for {slug} returned None")
            return None
        article = data[0]["article"]
        comments = Article.get_threads(slug)
        article["comments"] = comments
        return BlogArticle(**article)

    # TODO: Remove
    @staticmethod
    def as_blog_articles(data: List, article_key="article", concepts_key="concepts") -> List[BlogArticle]:
        """ Converts a List representing an article / articles and concepts to a List of BlogArticles.

        :returns: List of BlogArticles or None.
        """
        res = [
            BlogArticle(**item[article_key], concepts=item.get(concepts_key, []))
            for item in data
        ]
        return res

    # TODO: Test
    @classmethod
    def paginate_by_concept(cls, concept: str, endpoint: str, page: int = 0, per_page: int = 5, testing=False):
        """ Get a paginated object representing Articles containing a certain concept.

        :param concept: Concept
        :param endpoint: Flask view function name.
        :param page: The page number (0-indexed).
        :param per_page: Items per page.
        :param testing: If True, doesn't create _links to avoid the url_for function.
        :return: Paginated object or None.
        """
        query = """
            MATCH (concept: Concept {name: $concept})<-[rel:HAS_CONCEPT]-(article: Article)
            OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
            RETURN article{.*, concepts: concepts, categories: categories }
        """
        return cls._paginate_articles(base_query=query,
                                      endpoint=endpoint,
                                      page=page,
                                      per_page=per_page,
                                      testing=testing,
                                      query_params={"concept": concept},
                                      pagination_params={"concept": concept})

    @classmethod
    def paginate_by_category(cls, category: str, endpoint: str, page: int = 0, per_page: int = 5, testing=False):
        """ Get a paginated object representing Articles in a certain category.

        :param category: Category
        :param endpoint: Flask view function name.
        :param page: The page number (0-indexed).
        :param per_page: Items per page.
        :param testing: If True, doesn't create _links to avoid the url_for function.
        :return: Paginated object or None.
        """
        query = """
            MATCH (category: Category)<-[rel:HAS_CATEGORY]-(article: Article)
            OPTIONAL MATCH (article)-[:HAS_CONCEPT]-(category: Category)
            WHERE EXISTS ((:CATEGORY {name: $category})<-[:HAS_CATEGORY]-(article))
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
            RETURN article{.*, concepts: concepts, categories: categories }
        """
        return cls._paginate_articles(base_query=query,
                                      endpoint=endpoint,
                                      page=page,
                                      per_page=per_page,
                                      testing=testing,
                                      query_params={"category": category},
                                      pagination_params={"category": category})

    @classmethod
    def paginate_search(cls, search: str, endpoint: str, page: int = 0, per_page: int = 5, testing=False):
        """ Get a paginated object representing Article search results.

        :param search: Search term.
        :param endpoint: Flask view function name.
        :param page: The page number (0-indexed).
        :param per_page: Items per page.
        :param testing: If True, doesn't create _links to avoid the url_for function.
        :return: Paginated object or None.
        """

        # TODO: Requires FTS
        query = """
            CALL db.index.fulltext.queryNodes("articleContent", $search) YIELD node as article, score
            OPTIONAL MATCH (article: Article {published: True})-[rel:HAS_CONCEPT]->(concept: Concept)
            OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories, score
            RETURN article{.*, concepts: concepts, categories: categories }
            ORDER BY score DESC
        """
        return cls._paginate_articles(base_query=query,
                                      endpoint=endpoint,
                                      page=page,
                                      per_page=per_page,
                                      testing=testing,
                                      query_params={"search": search},
                                      pagination_params={"q": search})

    @classmethod
    def paginate_public(cls,
                        endpoint: str,
                        page: int = 0,
                        per_page: int = 5,
                        testing=False) -> Optional[Paginated]:
        """ Get a paginated object representing published Articles.

        :param endpoint: Flask view function name.
        :param page: The page number (0-indexed).
        :param per_page: Items per page.
        :param testing: If True, doesn't create _links to avoid the url_for function.
        :return: Paginated object or None.
        """

        query = """
            MATCH (article: Article { published: True })
            OPTIONAL MATCH (article: Article {published: True})-[rel:HAS_CONCEPT]->(concept: Concept)
            OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
            WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
            RETURN article{.*, concepts: concepts, categories: categories }
        """
        return cls._paginate_articles(base_query=query,
                                      endpoint=endpoint,
                                      page=page,
                                      per_page=per_page,
                                      testing=testing)

    @classmethod
    def _paginate_articles(cls, base_query: str,
                           endpoint: str,
                           page: int = 0,
                           per_page: int = 5,
                           testing=False,
                           include_comments=True,
                           query_params: Dict = {},
                           pagination_params: Dict = {}) -> Optional[Paginated]:
        """ Reusable Article pagination helper.

        Use kwargs for graph.run params.

        :param base_query: Main query excluding SKIP and LIMIT clauses.
        :param endpoint: Flask view function.
        :param page: The page number (0-indexed).
        :param per_page: Items per page.
        :param testing: If True, doesn't create _links to avoid the url_for function.
        :return: Dictionary or None.
        """
        # Pagination variables
        skip = page * per_page
        limit = per_page + 1

        # Get Articles
        query = f"""{base_query} 
                     SKIP $skip
                     LIMIT $limit
                 """
        data = graph.run(query, skip=skip, limit=limit, **query_params).data()
        if not data:
            # TODO: What to do
            pass

        data = [
            BlogArticle(**item["article"])
            for item in data
        ]

        if data and include_comments:
            for article in data:
                article.comments = Article.get_threads(article.slug)

        return Paginated(endpoint, data, page, per_page, testing, **pagination_params)

    @classmethod
    def get_threads(cls, slug: str) -> Optional[ArticleComments]:
        """ Get comment threads for Article.

        :param slug: Slug of the Article.
        :returns: List of CommentThreads or None.
        """

        # Check Article exists
        if not Article.exists(slug):
            print(f"Failed to get_threads because Article {slug} does not exist")
            return None

        # TODO: Requires APOC plugin
        query = """
            match r=(:Article {slug: $slug})<-[:AS_REPLY_TO*..]-(c:Comment)<-[:WROTE]-(u:User)
            WITH COLLECT(r) AS rs
            CALL apoc.convert.toTree(rs, true, {
                nodes: {
                    Comment: ['uuid', 'content', 'timestamp'],
                    User: ['username'],                     
                    Article: ['slug', 'timestamp']
                }
            }) yield value
            Return value
        """

        data = graph.run(query, slug=slug).data()

        if not data:
            return ArticleComments()

        data = data[0].get("value")

        if not data:
            return ArticleComments()

        comments = data["as_reply_to"]
        clean_comments = clean_comments_recursive(comments)
        return ArticleComments(clean_comments)


class Category(GraphObject):

    """ Simple 'folders' or tags for Articles.

    (c: Category)<-[:HAS_CATEGORY]-(a: Article)
    """

    name: str

    def __init__(self, name: str):
        self.name = name

    @classmethod
    def exists(cls, name: str):
        """ Check if a category with name exists.
        """
        query = """
            MATCH (c: Category {name: $name})
            RETURN c
        """
        return graph.evaluate(query, name=name) is not None

    @classmethod
    def get_categories(cls):
        """ Get categories, number of relationships.
        """
        query = """
            MATCH (category: Category)<-[:HAS_CATEGORY]-(a: Article)
            RETURN category{ .*, count: COUNT(a)} 
        """
        data = graph.run(query).data()
        if not data:
            return []
        return [
            item["category"]
            for item in data
        ]


class ConceptOrigin(Enum):

    """ Represents where a concept came from.
    """

    Me = 0
    ConceptNet = 1


# TODO: Relations between concepts based on the content text.
class Concept(GraphObject):
    """ Represents a Concept in an Article.

    (c: Concept)<-[:HAS_CONCEPT {mentions: [{start_char: int}]-(a: Article)

    (c: Concept)<-[:HAS_CONCEPT]-(a: Article)

    (first: Concept)-[:RELATED_TO { weight }]-(second: Concept)
    """
    __primarykey__ = "name"

    name: str = Property()
    content: str = Property()
    # TODO
    origin: ConceptOrigin

    def __init__(self, name, content: str = ""):
        """ Represents a concept / keyword / noun phrase mentioned in an article.
        """
        self.name = name
        self.content = content

    @classmethod
    def get_concept(cls, name: str) -> Optional[Dict]:
        """ Get concept by name.

        TODO: Includes connected article slugs.
        TODO: Related concepts / weights

        :return: True on success else False.
        """
        if not Concept.exists(name):
            logging.warning("Failed to get_concept because concept does not exist")
            return None
        query = """
            MATCH (concept: Concept {name: $name})
            RETURN concept
        """
        data = graph.run(query, name=name).data()
        if not data:
            logging.error("get_concept graph query returned None")
            return None
        return dict(data[0]["concept"])

    @classmethod
    def exists(cls, name) -> bool:
        """ Check if a concept with name exists.

        :return: True if exists else False.
        """
        query = """
            MATCH (c: Concept {name: $name})
            RETURN c
        """
        return graph.evaluate(query, name=name) is not None

    @classmethod
    def update_content(cls, name: str, content: str) -> bool:
        """ Update the content of a concept.

        :return: True if success else False.
        """
        if not Concept.exists(name):
            logging.warning("Attempted to update the content of a concept that does not exist")
            return False

        query = """
            MATCH (c: Concept {name: $name})
            SET c.content = $content
        """
        graph.run(query, name=name, content=content)
        logging.debug(f"Updated the content of concept {name}")
        return True

    @classmethod
    def get_concepts(cls):
        """ Get concepts, number of relationships.
        """
        query = """
            MATCH (concept: Concept)<-[:HAS_CONCEPT]-(a: Article)
            RETURN concept{ .*, count: COUNT(a)}
        """
        data = graph.run(query).data()
        if not data:
            return []
        return [
            item["concept"]
            for item in data
        ]


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


