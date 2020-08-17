from slugify import slugify
from . import graph
from typing import Optional, Dict, Any
from py2neo.ogm import GraphObject, Property
import datetime as dt
from ..html_parsing.concept_parser import parse_concepts


class Concept(GraphObject):
    """ Represents a Concept in an Article.

    (c: Concept)<-[:HAS_CONCEPT {mentions: [{start_char: int}]-(a: Article)

    (c: Concept)<-[:HAS_CONCEPT]-(a: Article)

    (first: Concept)-[:RELATED_TO { weight }]-(second: Concept)
    """

    __primarykey__ = "name"

    name: str = Property()
    content: str = Property()
    last_edited: str = Property()
    timestamp: str = Property()
    slug: str = Property()

    def __init__(self, name, content: str = ""):
        """ Represents a concept / keyword / noun phrase mentioned in an article.
        """
        self.name = name
        self.content = content
        self.timestamp = dt.datetime.now().isoformat()
        self.last_edited = self.timestamp
        self.slug = slugify(self.name)

    def to_dict(self):
        return {
            "name": self.name,
            "content": self.content,
            "last_edited": self.last_edited,
            "timestamp": self.timestamp,
            "slug": self.slug
        }

    def create(self) -> bool:

        """
        Create a concept
        :return:
        """

        if Concept.exists(self.name):
            return False

        graph.merge(self)
        Concept.add_related_concepts(self.name)
        return True

    @classmethod
    def get_concept(cls, name: str) -> Optional[Dict]:
        """ Get concept by name.

        :return: True on success else False.
        """
        if not Concept.exists(name):
            #logging.warning("Failed to get_concept because concept does not exist")
            return None
        query = """
            MATCH (concept: Concept {name: $name})
            RETURN concept
        """
        data = graph.run(query, name=name).data()
        if not data:
            #logging.error("get_concept graph query returned None")
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
    def update_concept(cls, name: str, content: str) -> bool:

        """ Update a concept
        :return:
        """

        if not Concept.exists(name):
            return False

        if not content:
            return False

        return Concept.__update_content(name, content)

    @classmethod
    def __update_content(cls, name: str, content: str) -> bool:

        tx = graph.begin()
        # 1. Delete concept relationships
        query = """
                MATCH (Concept)<-[rel:HAS_CONCEPT]-(Concept { name: $name })
                DELETE rel
            """
        graph.run(query, name=name)

        # 2. Update content and last_edited
        query = """
                MATCH (a: Concept { name: $name })
                SET a.content = $content
                SET a.last_edited = $last_edited
            """

        last_edited = dt.datetime.now().isoformat()
        graph.run(query, name=name, content=content, last_edited=last_edited)
        tx.commit()

        # 3. Update concept relationships
        Concept.add_related_concepts(name)
        return True

    @classmethod
    def add_related_concepts(cls, name: str):

        """ Add concept relations to the Article.
        """

        concept = Concept.match(graph).where(f"_.name = \'{name}\'").first()

        # Add concept net concepts
        related_concepts = parse_concepts(concept.content)
        if not related_concepts:
            return

        # Add concept relations to graph
        for related_concept in related_concepts:

            rel = Concept(related_concept.name, "")
            rel.create()

            query = """
                MERGE (related: Concept { name: $related_name })
                MERGE (main: Concept { name: $main_name })
                MERGE (main)-[:HAS_CONCEPT { mentions: $mentions }]->(related)
            """
            graph.run(query, main_name=name, mentions=related_concept.mentions, related_name=related_concept.name)

    @classmethod
    def get_concepts_in_articles(cls):
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

    @classmethod
    def get_all_concepts_with_linked(cls):

        """
        Get all concepts plus their (direct) links to other resources.
        :return:
        """

        # CYPHER expressionEngine=interpreted
        # Required due to bugs when using OPTIONAL MATCH with map projections
        query = """
            CYPHER expressionEngine=interpreted
            MATCH (c: Concept)
            OPTIONAL MATCH (c)<-[]-(n)
            WITH c as concept, collect(n) as links
            RETURN concept{.*, links: links}
        """

        data = graph.run(query).data()
        if not data:
            return []

        return [
            item["concept"]
            for item in data
        ]

    @classmethod
    def get_concepts(cls):
        """
        Get all concepts
        :return:
        """
        query = """
            MATCH (concept: Concept)
            RETURN concept
        """

        data = graph.run(query).data()
        if not data:
            return []

        return [
            item["concept"]
            for item in data
        ]

