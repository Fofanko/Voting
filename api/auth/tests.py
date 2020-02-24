import unittest
from api.base_tests import BaseTestCase
import json


class RegistrationTestCase(BaseTestCase):
    def test_empty_param(self):
        response = self.client.post('/registration')
        self.assertEqual(response.status_code, 400)

    def test_only_username_param(self):
        response = self.client.post('/registration', data={"username": "test_user"})
        self.assertEqual(response.status_code, 400)

    def test_only_password_param(self):
        response = self.client.post('/registration', data={"username": "test_password"})
        self.assertEqual(response.status_code, 400)

    def test_short_name(self):
        response = self.client.post('/registration', data={"username": "t", "password": "test_password"})
        response_data = json.loads(response.data.decode('utf8'))
        right_data = {"success": False, "data": {}, "error_msg": "Username must be longer than 2 letters, and less "
                                                                 "than 50"}
        self.assertEqual(response_data, right_data)

    def test_short_password(self):
        response = self.client.post('/registration', data={"username": "test_username", "password": "t"})
        response_data = json.loads(response.data.decode('utf8'))
        right_data = {"success": False, "data": {}, "error_msg": "Password must be longer than 3 letters"}
        self.assertEqual(response_data, right_data)

    def test_success_reg(self):
        response = self.client.post('/registration', data={"username": "test_username", "password": "test_password"})
        response_data = json.loads(response.data.decode('utf8'))
        right_data = {"success": True,
                      "data": {"auth_credentials": "dGVzdF91c2VybmFtZTp0ZXN0X3Bhc3N3b3Jk"},
                      "error_msg": None}
        self.assertEqual(response_data, right_data)

    def test_create_user_with_exist_username(self):
        self.client.post('/registration', data={"username": "test_username", "password": "test_password"})
        response = self.client.post('/registration', data={"username": "test_username", "password": "test_password"})
        response_data = json.loads(response.data.decode('utf8'))
        right_data = {"success": False,
                      "data": {},
                      "error_msg": "Username already exist"}
        self.assertEqual(response_data, right_data)


if __name__ == '__main__':
    unittest.main()
