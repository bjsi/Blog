from app.models.concept import Concept


def test_get_article_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/blog' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/articles')
    assert response.status_code == 200


def test_post_create_article(test_client):
    """
    GIVEN a Flask application
    WHEN the '/blog' page is requested (POST)
    THEN check the response is valid
    """

    title = "An Article"
    author = "Jamesb"
    content = "Some content."
    published = True
    finished_confidence = 5

    response = test_client.post('/articles', json={
        "title": title,
        "author": author,
        "content": content,
        "published": published,
        "finished_confidence": finished_confidence
    })

    assert response.status_code == 201


def test_post_create_article_add_related_concepts(test_client, test_graph):
    """
    GIVEN a Flask application
    WHEN the '/articles' page is requested (POST)
    THEN check the response is valid
    """

    title = "An Article"
    author = "Jamesb"

    concept_name = "Spaced Repetition"
    content = f"Some content about <span name='{concept_name}' class='concept'>spaced repetition</span>"
    published = True
    finished_confidence = 5

    response = test_client.post('/articles', json={
        "title": title,
        "author": author,
        "content": content,
        "published": published,
        "finished_confidence": finished_confidence
    })

    assert response.status_code == 201
    concept = Concept.get_concept(concept_name)
    assert concept is not None
    assert concept["name"] == concept_name


def test_post_update_article(test_client):
    """
    GIVEN a Flask application
    WHEN the '/blog' page is requested (POST)
    THEN check the response is valid
    """

    title = "An Article"
    author = "Jamesb"

    concept_name = "Spaced Repetition"
    content = f"Some content about <span name='{concept_name}' class='concept'>spaced repetition</span>"
    published = True
    finished_confidence = 5

    test_client.post('/blog', json={
        "title": title,
        "author": author,
        "content": content,
        "published": published,
        "finished_confidence": finished_confidence
    })

    content = f"This is a cool article"
    finished_confidence = 6

    response = test_client.post('/articles', json={
        "title": title,
        "author": author,
        "content": content,
        "published": published,
        "finished_confidence": finished_confidence
    })

    assert response.status_code == 201
    data = response.json
    assert data["content"] == content
    assert data["finished_confidence"] == finished_confidence
