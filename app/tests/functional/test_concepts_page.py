from app.models.concept import Concept


def test_get_concepts_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/blog' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/concepts')
    assert response.status_code == 200


def test_post_create_concept(test_client):
    """
    GIVEN a Flask application
    WHEN the '/concepts' page is requested (POST)
    THEN check the response is valid
    """

    name = "Abstraction"
    content = "Abstractions can be thought of as mental integrations."
    response = test_client.post('/concepts', json={"name": name, "content": content})

    assert response.status_code == 201
    assert response.json["name"] == name
    assert response.json["content"] == content


def test_post_create_concept_add_related(test_client, test_graph):
    """
    GIVEN a Flask application
    WHEN the '/concepts' page is requested (POST)
    THEN check the response is valid
    """

    name = "Abstraction"
    related_name = "Mental Integrations"
    content = f"Abstractions can be thought of as <span name='{related_name}' class='concept'>mental integrations</span>."
    response = test_client.post('concepts', json={"name": name, "content": content})

    assert response.status_code == 201
    assert response.json["name"] == name
    assert response.json["content"] == content

    related_concept = Concept.get_concept(related_name)
    assert related_concept is not None
    assert related_concept["name"] == related_name


def test_post_update_concept(test_client):
    """
    GIVEN a Flask application
    WHEN the '/concepts' page is requested (POST)
    THEN check the response is valid
    """

    name = "Abstraction"
    content = "Abstractions can be thought of as mental integrations."
    test_client.post('/concepts', json={"name": name, "content": content})

    content = "Hello World"
    response = test_client.post('/concepts', json={"name": name, "content": content})

    assert response.status_code == 201
    assert response.json["name"] == name
    assert response.json["content"] == content
