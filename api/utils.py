from flask_restful import Resource, abort, request
from functools import wraps

from api.auth.models import basic_authentication


class BasicResource(Resource):
    """
        Базовый класс ресурса, содержащий куклу ответа
    """
    def __init__(self):
        super().__init__()
        self.response = {
            "success": None,
            "data": {},
            "error_msg": None
        }


def user_required(func):
    """
        Wrapper for check is user authentication
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_info = request.headers.get('WWW-Authenticate', None)
        if auth_info is None:
            abort(401)
        if basic_authentication(auth_info):
            return func(*args, **kwargs)
        abort(401)

    return wrapper


class SecureResource(BasicResource):
    """
        Класс ресурса для запросов требующих авторизацию
        по Basic Auth
    """
    method_decorators = [user_required]


class Field:
    pass


class CharField(Field):
    pass
