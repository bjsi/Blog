def test_get_rss_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/rss' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/rss')
    assert response.status_code == 200

