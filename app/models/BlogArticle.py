from typing import List, Dict
from app.models.comments import ArticleComments


class BlogArticle:

    """ Article and Comment threads.
    """

    published: bool
    title: str
    uuid: str
    content: str
    slug: str
    timestamp: str
    author: str
    concepts: List[Dict[str, str]]
    last_edited: str
    categories: List[str]
    finished_confidence: int
    summary: str

    comments: ArticleComments

    def __init__(self,
                 published: bool,
                 title: str,
                 uuid: str,
                 content: str,
                 categories: List[str],
                 finished_confidence: int,
                 slug: str,
                 timestamp: str,
                 author: str,
                 concepts: List[Dict[str, str]],
                 last_edited: str,
                 summary: str,
                 comments: ArticleComments = ArticleComments()) -> None:

        self.published = published
        self.author = author
        self.title = title
        self.uuid = uuid
        self.content = content
        self.slug = slug
        self.timestamp = timestamp
        self.concepts = concepts
        self.last_edited = last_edited
        self.comments = comments
        self.categories = categories
        self.summary = summary
        self.finished_confidence = finished_confidence
