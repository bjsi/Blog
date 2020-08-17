def test_get_about_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/blog' page is requested (GET)
    THEN check the response is valid
    """

    response = test_client.get('/about')
    assert response.status_code == 200

