# Models
from app.models.article import Article

# flask
from flask import current_app as app, make_response, url_for
from feedgen.feed import FeedGenerator

import dateutil.parser
import datetime as dt

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


@app.route('/rss')
def rss():
    fg = FeedGenerator()
    fg.title('Experimental Learning')
    fg.description(r"Jamesb's articles on learning")
    fg.link(href='https://experimental-learning.com')

    for article in Article.get_public():
        url = "https://experimental-learning.com/articles/" + article["slug"]
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=url)
        fe.description(convert_urls(article["content"]))
        fe.guid(url, permalink=True)
        fe.author(name=article["author"], email="experimentallearning0@gmail.com")
        fe.pubDate(dateutil.parser.parse(article["timestamp"]).replace(tzinfo=dt.timezone.utc))

    response = make_response(fg.rss_str())
    response.headers.set('Content-Type', 'application/rss+xml')

    return response


def convert_urls(content: str) -> str:
    soup = BeautifulSoup(content)

    for url in soup.find_all('a'):
        href = url.get("href")
        if href and is_relative(href):
            url["href"] = rel_to_abs(href)

    for url in soup.find_all('img'):
        href = url.get("src")
        if href and is_relative(href):
            url["src"] = rel_to_abs(href)

    return str(soup)


def is_relative(href: str) -> bool:
    return not bool(urlparse(href).netloc)


def rel_to_abs(rel_url: str):
    return requests.compat.urljoin("https://experimental-learning.com", rel_url)

