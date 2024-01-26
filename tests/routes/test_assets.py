import unittest
import json
import io
from datetime import datetime
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
        json_data = {"username": "test1", "password": "test"}
        jwt_response = self.client.post("/auth/signup", json=json_data)
        self.jwt = json.loads(jwt_response.get_data(as_text=True)).get("jwt")

    def tearDown(self):
        self.database.drop_all_tables()
        self.app = None
        self.client = None
        self.jwt = None

    def test_add_asset(self):
        current_date = datetime.now()
        acquired_date = current_date.strftime("%Y-%m-%d")
        asset_data = {
            "name": "test",
            "asset_sn": "test",
            "description": "test",
            "acquired_date": acquired_date,
            "jwt": self.jwt,
            "file": (io.BytesIO(b"this is a test"), "test.pdf"),
        }

        response = self.client.post(
            "/assets/asset_add", data=asset_data, content_type="multipart/form-data"
        )
        json_response = json.loads(response.get_data(as_text=True)).get("message")
        assert json_response == "Successfully created asset test"
        assert response.status_code == 200

    def test_get_all_assets(self):
        current_date = datetime.now()
        acquired_date = current_date.strftime("%Y-%m-%d")
        asset_data = {
            "name": "test",
            "asset_sn": "test",
            "description": "test",
            "acquired_date": acquired_date,
            "jwt": self.jwt,
            "file": (io.BytesIO(b"this is a test"), "test.pdf"),
        }

        self.client.post(
            "/assets/asset_add", data=asset_data, content_type="multipart/form-data"
        )
        data = {"jwt": self.jwt}
        response = self.client.get(
            "/assets/asset_all", json=data, content_type="application/json"
        )
        json_response = json.loads(response.get_data(as_text=True))[0]
        assert json_response.get("name") == "test"
        assert json_response.get("asset_sn") == "test"
        assert json_response.get("description") == "test"
        assert json_response.get("acquired_date") == acquired_date
        assert response.status_code == 200
