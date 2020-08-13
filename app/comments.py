from typing import List, Dict


class CommentThread:

    """ Represents a comment in a thread.
    """

    content: str
    author: str  # Username of the user that wrote the Comment
    children: List["CommentThread"]
    timestamp: str

    def __init__(self, uuid: str, content: str, author: str, timestamp: str, children: List["CommentThread"]):
        self.uuid = uuid
        self.content = content
        self.author = author
        self.children = children
        self.timestamp = timestamp

    def __repr__(self):
        return f"<ThreadComment: content={self.content[:10]}... author={self.author} children={len(self.children)}>"


def clean_comments_recursive(comments: List[Dict]) -> List[CommentThread]:
    """ Called recursively to create a list of root Comment threads on an Article.

    :param comments: The messy Neo4j DB response.
    :returns: A list of CommentThread objects
    """
    thread_comments = []
    if comments:
        comments.sort(key=lambda x: x["timestamp"])
    for comment in comments:
        children = comment.get("as_reply_to", [])
        thread_comment = CommentThread(
            uuid=comment["uuid"],
            content=comment["content"],
            author=comment["wrote"][0]["username"],
            timestamp=comment["timestamp"],
            children=clean_comments_recursive(children)
        )
        thread_comments.append(thread_comment)
    return thread_comments


class ArticleComments:

    """ Represents all comment threads on an Article.
    """

    threads: List[CommentThread]
    count: int

    def __init__(self, threads: List[CommentThread] = []):
        self.threads = threads
        self.count = self.count_comments(threads)

    # TODO: Needs more testing
    def count_comments(self, threads: List[CommentThread], count: int = 0) -> int:
        """ Recursively count the number of comments.
        """
        for thread in threads:
            count += 1  # The comment
            count += len(thread.children)  # comment's children
            for child in thread.children:  # call recursively
                count += self.count_comments(child.children)
        return count




