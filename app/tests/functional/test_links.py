def test_get_links_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/blog' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/links')
    assert response.status_code == 200


def test_post_create_link(test_client):
    """
    GIVEN a Flask application
    WHEN the '/concepts' page is requested (POST)
    THEN check the response is valid
    """

    url = "https://experimental-learning.com"
    title = "Experimental Learning"
    author = "Jamesb"
    content = "Cool website about learning"

    response = test_client.post('/links', json={
        "url": url,
        "title": title,
        "author": author,
        "content": content
    })
    assert response.status_code == 201


def test_post_create_link_add_related_concepts(test_client, test_graph):
    """
    GIVEN a Flask application
    WHEN the '/concepts' page is requested (POST)
    THEN check the response is valid
    """

    url = "https://experimental-learning.com"
    title = "Experimental Learning"
    author = "Jamesb"
    content = "Cool website about <span name='Spaced Repetition' class='concept'>spaced repetition</span>."

    response = test_client.post('/links', json={
        "url": url,
        "title": title,
        "author": author,
        "content": content
    })

    assert response.status_code == 201

    data = response.json

    assert data["url"] == url
    assert data["title"] == title
    assert data["author"] == author
    assert data["content"] == content


def test_post_update_link(test_client, test_graph):
    url = "https://experimental-learning.com"
    title = "Experimental Learning"
    author = "Jamesb"
    content = "Cool website about <span name='Spaced Repetition' class='concept'>spaced repetition</span>."

    test_client.post('/links', json={
        "url": url,
        "title": title,
        "author": author,
        "content": content
    })

    content = "Cool website"

    response = test_client.post('/links', json={
        "url": url,
        "title": title,
        "author": author,
        "content": content
    })

    assert response.status_code == 201
    data = response.json
    assert data["url"] == url
    assert data["title"] == title
    assert data["author"] == author
    assert data["content"] == content
