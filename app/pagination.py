from flask import url_for
from typing import List, Any


class Meta:

    """ Meta info about the Paginated object.
    """

    current_page: int
    items_per_page: int

    def __init__(self, current_page: int, items_per_page: int):
        self.current_page = current_page
        self.items_per_page = items_per_page

    def __repr__(self):
        return f"<Meta: page={self.current_page} per_page={self.items_per_page}>"


class Links:

    """ Page links for the Paginated object.
    """

    current_page: str
    next_page: str
    prev_page: str

    def __init__(self, endpoint: str, page: int, per_page: int, has_next: bool, testing: bool = False, **kwargs):
        self.current_page = url_for(endpoint, page=page, per_page=per_page, **kwargs) \
                                if not testing \
                                else None
        self.next_page = url_for(endpoint, page=page + 1, per_page=per_page, **kwargs) \
                            if not testing and has_next \
                            else None
        self.prev_page = url_for(endpoint, page=page - 1, per_page=per_page, **kwargs) \
                            if not testing and page != 0 \
                            else None

    def __repr__(self):
        return f"<Links: current={self.current_page} next={self.next_page} prev={self.prev_page}>"


class Paginated:

    """
    Represents a collection of paginated items.
    """

    data: List[Any]
    meta: Meta
    links: Links

    def __init__(self, endpoint: str, data: List[Any], page: int, per_page: int, testing=False, **kwargs):
        has_next = len(data) > per_page
        if has_next:
            data = data[:-1]
        self.data = data
        self.meta = Meta(page, per_page)
        self.links = Links(endpoint, page, per_page, has_next, testing, **kwargs)

    def __repr__(self):
        return f"<Paginated: items={len(self.data)}>"


