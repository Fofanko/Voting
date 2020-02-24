from api.utils import BasicResource
from flask_restful import reqparse
from .models import User


class Registration(BasicResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, help="Username is required", required=True)
        parser.add_argument('password', type=str, help="Password is required", required=True)
        args = parser.parse_args()
        username, raw_password = args["username"], args["password"]

        if len(username) <= 3 or len(username) >= 50:
            self.response['success'] = False
            self.response['error_msg'] = "Username must be longer than 2 letters, and less than 50"
            return self.response, 400

        if len(raw_password) <= 3:
            self.response['success'] = False
            self.response['error_msg'] = "Password must be longer than 3 letters"
            return self.response, 400
        user = User(username, raw_password)
        # check if username exist
        # if user not exist return error
        if user.is_username_exist():
            self.response["success"] = False
            self.response["error_msg"] = "Username already exist"
            return self.response, 401

        user.save()
        self.response["success"] = True
        self.response["data"] = {
            "auth_credentials": user.get_credentials()
        }
        return self.response
