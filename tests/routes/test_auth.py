import unittest
import json
import os

from common.configuration import create_app

os.environ["DATABASETYPE"] = "TESTING"
os.environ["APP_SETTINGS"] = "common.base.TestingConfig"
os.environ["TESTING"] = "true"


class TestAssets(unittest.TestCase):
    def setUp(self):
        self.app, self.database = create_app()
        self.app.config["current_db"] = self.database.db
        self.database.init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        self.database.drop_all_tables()
        self.app = None
        self.client = None

    def test_add_user(self):
        json_data = {"username": "test1", "password": "test"}
        signup_response = self.client.post("/auth/signup", json=json_data)
        self.jwt = json.loads(signup_response.get_data(as_text=True)).get("jwt")
        assert signup_response.status_code == 200
        assert self.jwt != None

    def test_login_user(self):
        json_data = {"username": "test1", "password": "test"}
        self.client.post("/auth/signup", json=json_data)
        login_response = self.client.post("/auth/login", json=json_data)
        self.jwt = json.loads(login_response.get_data(as_text=True)).get("jwt")
        assert self.jwt != None
        assert login_response.status_code == 200
