from typing import List

import uuid
from . import graph
from py2neo.ogm import GraphObject, Property
import logging

from ..html_parsing.concept_parser import parse_concepts


class Podcast(GraphObject):

    """Represents a Golden Nuggets Podcast episode.
    """

    uuid: str = Property()
    title: str = Property()
    date: str = Property()
    url: str = Property()
    transcript: str = Property()
    description: str = Property()
    feedback: str = Property()

    def __init__(self, title: str, date: str, url: str, description: str) -> None:
        self.title = title
        self.description = description
        self.date = date
        self.url = url
        self.uuid = str(uuid.uuid4())

    @classmethod
    def get_public(cls) -> List["Podcast"]:

        """ Returns list of podcasts
        :return:
        """

        query = """
            MATCH (podcast: Podcast)
            OPTIONAL MATCH (podcast: Podcast)-[rel: HAS_CONCEPT]->(concept: Concept)
            WITH COLLECT (rel {.*, name: concept.name}) as concepts, podcast
            RETURN podcast {.*, concepts: concepts }
        """

        data = graph.run(query).data()
        if not data:
            return []
        return [
            item["podcast"]
            for item in data
        ]

    @classmethod
    def add_concepts(cls, title: str):

        """ Add concept relations to the Article.
        """

        if not Podcast.exists(title):
            logging.warning(f"Failed to add concepts because Article does not exist")
            return

        note = Podcast.match(graph).where(f"_.title = \'{title}\'").first()

        # Add concept net concepts
        related_concepts = parse_concepts(note.content)
        if not related_concepts:
            return

        # Add concept relations to graph
        for related_concept in related_concepts:
            query = """
                    MERGE (related: Concept { name: $related_name })
                    MERGE (podcast: Podcast { title: $title })
                    MERGE (podcast)-[:HAS_CONCEPT { mentions: $mentions }]->(related)
                """
            graph.run(query, title=title, mentions=related_concept.mentions, related_name=related_concept.name)

    @classmethod
    def exists(cls, title: str):

        """ Checks if Podcast exists.

        :return: True if exists else False.
        """

        query = """
            MATCH (p: Podcast { title: $title })
            RETURN p
        """

        return graph.evaluate(query, title=title) is not None

    def create(self):

        """
        Add a new podcast
        :return:
        """

        if Podcast.exists(self.title):
            return

        graph.create(self)
        logging.debug(f"Created new podcast with uuid {self.uuid}")
