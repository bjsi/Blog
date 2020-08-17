from typing import Optional, List, Any, Dict
import uuid
from py2neo.ogm import GraphObject, Property
import datetime as dt
from slugify import slugify
from app.models.BlogArticle import BlogArticle
from app.models.comments import clean_comments_recursive, ArticleComments
from app.html_parsing.concept_parser import parse_concepts
from app.models.pagination import Paginated
from app.html_parsing.summary_parser import parse_summary
import logging
from . import graph
from .concept import Concept


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

    def to_dict(self):
        return {

            "title": self.title,
            "content": self.content,
            "published": self.published,
            "author": self.author,
            "finished_confidence": self.finished_confidence,
            "timestamp": self.timestamp,
            "last_edited": self.last_edited,
            "slug": self.slug

        }

    @classmethod
    def add_concepts(cls, title: str) -> None:

        """ Add concept relations to the Article.
        """

        article = Article.match(graph).where(f"_.title = \'{title}\'").first()

        # Add concept net concepts
        concepts = parse_concepts(article.content)
        if not concepts:
            return

        # Add concept relations to graph
        for concept in concepts:

            rel = Concept(concept.name, "")
            rel.create()

            # Add concept
            query = """
                MERGE (c: Concept { name: $name })
                MERGE (a: Article { uuid: $uuid })
                MERGE (a)-[:HAS_CONCEPT { mentions: $mentions }]->(c)
            """
            graph.run(query, name=concept.name, mentions=concept.mentions, uuid=article.uuid)
            logging.debug(f"Added Article-Concept relationship between {article.title} and {concept.name}")

    def create(self) -> bool:

        """ Create an Article and add concept relations.

        :returns: True on success else False.
        """

        # Check uniqueness
        if Article.exists(self.title):
            logging.warning(f"Failed to create new article \'{self.title}\' because an article with that slug already exists.")
            return False

        # Get summary information
        self.summary = parse_summary(self.content)

        # Create article
        graph.merge(self)
        logging.debug(f"Created new Article {self.title}")

        # Add relationships
        Article.add_concepts(self.title)
        return True

    @classmethod
    def update_article(cls, title: str, update_info: Dict[str, Any]) -> bool:
        """ Update an article's properties.

        Ignores slug.
        Ignores new properties.

        :return: True on success else False.
        """
        if not Article.exists(title):
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
                Article.__update_content(title, value)
            elif key == "slug" or key == "title":
                continue
            else:
                Article.__update_property(title, key, value)
        return True

    @classmethod
    def __update_property(cls, title: str, key: str, value: Any) -> bool:
        """
        :param slug: Article slug.
        :param value: New value.
        :return: True on success else False.
        """
        if not Article.exists(title):
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
            WHERE a.title = $title
            SET a.{key} = $value
        """
        graph.run(query, title=title, value=value)
        logging.debug(f"Updated {key} field of {title} to {value}")
        return True

    @classmethod
    def __update_content(cls, title: str, value) -> bool:
        """ Update the content of an existing article.

        :param slug: Article slug.
        :param value: New article content.
        :return: True on success else False.
        """
        if not Article.exists(title):
            return False
        try:

            # Get categories and summary
            summary = parse_summary(value)

            tx = graph.begin()
            # 1. Delete concept relationships
            query = """
                MATCH (Concept)<-[rel:HAS_CONCEPT]-(Article { title: $title })
                DELETE rel
            """
            graph.run(query, title=title)

            # 2. Update content and last_edited
            query = """
                MATCH (a: Article { title: $title })
                SET a.content = $content
                SET a.last_edited = $last_edited
                SET a.summary = $summary
            """

            last_edited = dt.datetime.now().isoformat()
            graph.run(query, content=value, summary=summary, last_edited=last_edited, title=title)
            tx.commit()
            logging.debug(f"Updated content for Article {title}")

            # 3. Update concept relationships
            Article.add_concepts(title)
            return True

        except Exception as e:
            logging.error(f"Failed to update content with exception {e}")
            return False

    @classmethod
    def exists(cls, title: str) -> bool:
        """ Checks if an Article exists.

        :return: True if exists else False.
        """
        query = """
            MATCH (a: Article { title: $title })
            RETURN a
        """
        return graph.evaluate(query, title=title) is not None

    # TODO: Test
    @classmethod
    def get_public(cls) -> List:
        """ Get all published Articles.

        :return: A List representing all published Articles.
        """

        query = """
            CYPHER expressionEngine=interpreted
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
            CYPHER expressionEngine=interpreted
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
            CYPHER expressionEngine=interpreted
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

    @classmethod
    def get_article(cls, title: str = None, slug: str = None) -> Optional[BlogArticle]:
        """ Get Article by slug name.

        :return: BlogArticle or None.
        """

        if title:

            query = """
                CYPHER expressionEngine=interpreted
                MATCH (article: Article { title: $title })
                OPTIONAL MATCH (article: Article {title: $title})-[rel:HAS_CONCEPT]->(concept: Concept)
                OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
                WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
                RETURN article{.*, concepts: concepts, categories: categories }
            """
            data = graph.run(query, title=title).data()
            if not data:
                return None

        elif slug:

            query = """
                CYPHER expressionEngine=interpreted
                MATCH (article: Article { slug: $slug })
                OPTIONAL MATCH (article: Article {slug: $slug})-[rel:HAS_CONCEPT]->(concept: Concept)
                OPTIONAL MATCH (article)-[:HAS_CATEGORY]-(category: Category)
                WITH COLLECT(rel{.*, name: concept.name}) as concepts, article, COLLECT(category) as categories
                RETURN article{.*, concepts: concepts, categories: categories }
            """
            data = graph.run(query, slug=slug).data()
            if not data:
                return None

        article = data[0]["article"]
        comments = Article.get_threads(title)
        article["comments"] = comments
        return BlogArticle(**article)

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
            CYPHER expressionEngine=interpreted
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
            CYPHER expressionEngine=interpreted
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
            CYPHER expressionEngine=interpreted
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
                article.comments = Article.get_threads(article.title)

        return Paginated(endpoint, data, page, per_page, testing, **pagination_params)

    @classmethod
    def get_threads(cls, title: str) -> Optional[ArticleComments]:
        """ Get comment threads for Article.

        :param slug: Slug of the Article.
        :returns: List of CommentThreads or None.
        """

        # Check Article exists
        if not Article.exists(title):
            return None

        query = """
            match r=(:Article {title: $title})<-[:AS_REPLY_TO*..]-(c:Comment)<-[:WROTE]-(u:User)
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

        data = graph.run(query, title=title).data()

        if not data:
            return ArticleComments()

        data = data[0].get("value")

        if not data:
            return ArticleComments()

        comments = data["as_reply_to"]
        clean_comments = clean_comments_recursive(comments)
        return ArticleComments(clean_comments)
