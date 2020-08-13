import os
import unittest
from app.models import graph
from app import create_app


app = create_app()


class BasicTests(unittest.TestCase):

    def setUp(self) -> None:
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # detach delete neo4j ?
        self.assertFalse(app.debug)
        self.app = app.test_client()

    def tearDown(self) -> None:
        pass

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
