from typing import List, NamedTuple
from bs4 import BeautifulSoup


class CategoriesParsed(NamedTuple):

    """ New content with categories removed into List
    """

    content: str
    categories: List[str]

    def __repr__(self):
        return f"<CategoriesParsed: count={len(self.categories)} >"


def remove_categories(content: str) -> str:
    """ Remove the categories from an html string.

    :param content:
    :return:
    """
    soup = BeautifulSoup(content, 'html.parser')
    categories = soup.find_all("span", class_="category")
    for category in categories:
        category.extract()
    return str(soup)


def get_categories(content: str) -> List[str]:
    """ Get categories from an html string.

    :param content: Article content
    :return: List of Categories or None
    """
    # Parse html
    soup = BeautifulSoup(content, 'html.parser')
    return [
        category.string
        for category in soup.find_all("span", class_="category")
    ]




