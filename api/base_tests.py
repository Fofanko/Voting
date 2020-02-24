import unittest
from . import create_app
from api.migrate import clear_db, migrate_db


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(test_config=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            clear_db()
            migrate_db()

    def tearDown(self):
        pass
