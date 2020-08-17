import logging

from typing import Any, Dict, List, Optional
import datetime as dt
from . import graph
from py2neo.ogm import GraphObject, Property

from ..html_parsing.concept_parser import parse_concepts


class Link(GraphObject):

    """ Represents a link shared on the links page.
    """

    __primarykey__ = "title"

    url: str = Property()
    title: str = Property()
    author: str = Property()
    content: str = Property()
    last_edited: str = Property()
    timestamp: str = Property()

    def __init__(self, url: str, title: str, author: str, content: str):
        self.url = url
        self.title = title
        self.author = author
        self.content = content
        self.timestamp = dt.datetime.now().isoformat()
        self.last_edited = self.timestamp

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "content": self.content,
            "last_edited": self.last_edited,
            "timestamp": self.timestamp
        }

    @classmethod
    def update_link(cls, title: str, update_info: Dict[str, Any]) -> bool:
        """ Update a link
        :return:
        """

        if not Link.exists(title):
            return False

        if not update_info:
            return False

        link_fields = list(vars(Link)["__annotations__"].keys())
        for key, value in update_info.items():
            # Don't allow adding new properties
            if key not in link_fields:
                continue

            elif key == "content":
                Link.__update_content(title, value)
            elif key == "slug" or key == "title":
                continue
            else:
                Link.__update_property(title, key, value)

        return True

    @classmethod
    def __update_property(cls, title: str, key: str, value: Any) -> bool:

        query = f"""
            MATCH (link: Link)
            WHERE link.title = $title
            SET link.{key} = $value
        """

        graph.run(query, title=title, value=value)
        return True

    @classmethod
    def __update_content(cls, title: str, content: str) -> bool:

        tx = graph.begin()
        # 1. Delete concept relationships
        query = """
            MATCH (Concept)<-[rel:HAS_CONCEPT]-(Link { title: $title })
            DELETE rel
        """
        graph.run(query, title=title)

        # 2. Update content and last_edited
        query = """
            MATCH (a: Link { title: $title })
            SET a.content = $content
            SET a.last_edited = $last_edited
        """

        last_edited = dt.datetime.now().isoformat()
        graph.run(query, title=title, content=content, last_edited=last_edited)
        tx.commit()

        # 3. Update concept relationships
        Link.add_related_concepts(title)
        return True

    @classmethod
    def get_link(cls, title: str) -> Optional[Dict]:

        """
        :return:
        """
        if not Link.exists(title):
            return None

        query = """
            MATCH (link: Link {title: $title})
            RETURN link
        """

        data = graph.run(query, title=title).data()
        if not data:
            return None
        return dict(data[0]["link"])

    @classmethod
    def get_links(cls) -> List["Link"]:

        """ Get all published Links
        """

        query = """
            MATCH (link: Link)
            OPTIONAL MATCH (link: Link)-[rel: HAS_CONCEPT]->(concept: Concept)
            WITH COLLECT(rel {.*, name: concept.name}) as concepts, link
            RETURN link {.*, concepts}
        """

        data = graph.run(query).data()
        if not data:
            return []

        return [
            item["link"]
            for item in data
        ]

    @classmethod
    def add_related_concepts(cls, title: str):

        """ Add concept relations to the Article.
        """

        link = Link.match(graph).where(f"_.title = \'{title}\'").first()

        # Add concept net concepts
        related_concepts = parse_concepts(link.content)
        if not related_concepts:
            return

        # Add concept relations to graph
        for related_concept in related_concepts:

            query = """
                MERGE (related: Concept { name: $related_name })
                MERGE (link: Link { title: $title })
                MERGE (link)-[:HAS_CONCEPT { mentions: $mentions }]->(related)
            """
            graph.run(query, title=title, mentions=related_concept.mentions, related_name=related_concept.name)

    @classmethod
    def exists(cls, title: str) -> bool:

        """
        Check if a link with title exists
        :param title:
        :return:
        """

        query = """
            MATCH (c: Link {title: $title})
            RETURN c
        """
        return graph.evaluate(query, title=title) is not None

    def create(self) -> bool:

        """
        Create a link
        :return:
        """

        if Link.exists(self.title):
            return False

        graph.create(self)
        Link.add_related_concepts(self.title)
        return True


