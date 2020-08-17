from py2neo.ogm import GraphObject, Property
from . import graph
import datetime as dt

from .concept import Concept
from ..html_parsing.concept_parser import parse_concepts


class Note(GraphObject):

    """Represents one of my working notes.
    """

    __primarykey__ = "title"

    title: str = Property()
    content: str = Property()
    timestamp: str = Property()
    last_edited: str = Property()
    slug: str = Property()

    def __init__(self, title: str, content: str) -> None:
        self.title = title
        self.content = content
        self.timestamp = dt.datetime.now().isoformat()
        self.last_edited = self.timestamp

    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "timestamp": self.timestamp,
            "last_edited": self.last_edited
        }

    @classmethod
    def get_note(cls, title: str):
        if not Note.exists(title):
            return None

        query = """
            MATCH (note: Note {title: $title})
            RETURN note
        """

        data = graph.run(query, title=title).data()
        if not data:
            return None
        return dict(data[0]["note"])

    @classmethod
    def get_public(cls):

        query = """
            MATCH (note: Note)
            OPTIONAL MATCH (note: Note)-[rel: HAS_CONCEPT]->(concept: Concept)
            WITH COLLECT(rel {.*, name: concept.name}) as concepts, note
            RETURN note {.*, concepts}
        """

        data = graph.run(query).data()
        if not data:
            return []

        return [
            item["note"]
            for item in data
        ]

    @classmethod
    def update_note(cls, title: str, content: str) -> bool:

        """ Update a note
        :return:
        """

        if not Note.exists(title):
            return False

        if not content:
            return False

        Note.__update_content(title, content)
        return True

    @classmethod
    def __update_content(cls, title: str, content: str) -> bool:

        tx = graph.begin()
        # 1. Delete concept relationships
        query = """
            MATCH (Concept)<-[rel:HAS_CONCEPT]-(Note { title: $title })
            DELETE rel
        """
        graph.run(query, title=title)

        # 2. Update content and last_edited
        query = """
            MATCH (a: Note { title: $title })
            SET a.content = $content
            SET a.last_edited = $last_edited
        """

        last_edited = dt.datetime.now().isoformat()
        graph.run(query, title=title, content=content, last_edited=last_edited)
        tx.commit()

        # 3. Update concept relationships
        Note.add_related_concepts(title)
        return True

    def create(self) -> bool:

        """ Create a new Note
        """

        if Note.exists(self.title):
            return False

        graph.create(self)
        Note.add_related_concepts(self.title)
        return True

    @classmethod
    def add_related_concepts(cls, title: str):

        """ Add concept relations to the Article.
        """

        note = Note.match(graph).where(f"_.title = \'{title}\'").first()

        # Add concept net concepts
        related_concepts = parse_concepts(note.content)
        if not related_concepts:
            return

        # Add concept relations to graph
        for related_concept in related_concepts:

            rel = Concept(related_concept.name, "")
            rel.create()

            query = """
                MERGE (related: Concept { name: $related_name })
                MERGE (note: Note { title: $title })
                MERGE (note)-[:HAS_CONCEPT { mentions: $mentions }]->(related)
            """
            graph.run(query, title=title, mentions=related_concept.mentions, related_name=related_concept.name)

    @classmethod
    def exists(cls, title: str) -> bool:

        """
        Checks if a note already exists based on the element id.

        :param title:
        :return: True if exists else False.
        """

        query = """
            MATCH (p: Note { title: $title })
            RETURN p
        """

        return graph.evaluate(query, title=title) is not None
