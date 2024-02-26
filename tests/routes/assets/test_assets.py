import unittest
import json
import io
from datetime import datetime
from tests.base import BaseTest

class TestAssets(BaseTest):
    
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
