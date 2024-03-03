from tests.base import BaseTest
import json


class TestAssets(BaseTest):
    def test_login_user(self):
        login_response = self.client.post("/auth/login", json=self.user_signup_data)
        self.jwt = json.loads(login_response.get_data(as_text=True)).get("jwt")
        assert self.jwt != None
        assert login_response.status_code == 200
