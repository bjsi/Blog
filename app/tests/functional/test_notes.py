def test_get_notes_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/notes' page is requested (GET)
    THEN check the response is valid
    """

    response = test_client.get('/notes')
    assert response.status_code == 200


def test_post_create_note(test_client):
    """
    GIVEN a Flask application
    WHEN the '/notes' page is requested (POST)
    THEN check the response is valid
    """

    title = "This is a note"
    content = "A cool note"

    response = test_client.post('/notes', json={
        "title": title,
        "content": content
    })

    assert response.status_code == 201


def test_post_create_note_add_related_concepts(test_client, test_graph):
    """
    GIVEN a Flask application
    WHEN the '/concepts' page is requested (POST)
    THEN check the response is valid
    """

    title = "This is a note"
    content = "A cool note about <span class='concept' name='Spaced Repetition'>spaced repetition</span>."

    response = test_client.post('/notes', json={
        "title": title,
        "content": content
    })

    assert response.status_code == 201


def test_post_update_note(test_client, test_graph):

    title = "Experimental Learning"
    content = "Cool website about <span name='Spaced Repetition' class='concept'>spaced repetition</span>."

    test_client.post('/notes', json={
        "title": title,
        "content": content
    })

    content = "Cool website"

    response = test_client.post('/notes', json={
        "title": title,
        "content": content
    })

    assert response.status_code == 201
    data = response.json
    assert data["title"] == title
    assert data["content"] == content
