import unittest
import json
import os
from common.configuration import create_app

class BaseTest(unittest.TestCase):
    def setUp(self):
        os.environ["DATABASETYPE"] = "TESTING"
        os.environ["APP_SETTINGS"] = "common.base.TestingConfig"
        os.environ["TESTING"] = "true"
        self.app, self.database = create_app()
        self.app.config["current_db"] = self.database.db
        self.database.init_db()
        self.client = self.app.test_client()
        self.user_signup_data = {"username": "test1", "password": "test"}
        jwt_response = self.client.post("/auth/signup", json=self.user_signup_data)
        self.jwt = json.loads(jwt_response.get_data(as_text=True)).get("jwt")
    
    def tearDown(self):
        self.database.drop_all_tables()
        self.app = None
        self.client = None
        self.jwt = None