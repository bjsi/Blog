import pytest
from app import create_app
from app.models import graph
from app.models.concept import Concept


def create_concepts():
    c1 = Concept("SuperMemo", "An SRS program.")
    c1.create()


@pytest.fixture(scope='module')
def test_client():

    flask_app = create_app()
    testing_client = flask_app.test_client()

    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client

    ctx.pop()


@pytest.fixture(scope='session', autouse=True)
def test_graph():
    # Clean db
    graph.evaluate("MATCH (n) DETACH DELETE n")

    yield graph

    graph.evaluate("MATCH (n) DETACH DELETE n")

