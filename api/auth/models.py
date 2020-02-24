from base64 import b64decode, b64encode

from api.db import get_db
from hashlib import md5
from flask import g


def basic_authentication(auth_info):
    user = User.get_user_from_basic_auth(auth_info)
    if user is None or user.is_user_exist():
        return False
    g.user = user
    return True


class User:
    is_new = True
    pk = None

    def __init__(self, username, password, password_hash=False):
        """
        :param username: Имя пользователя
        :param password: Пароль
        :param password_hash: Является ли пароль хешем
        """
        self.username = username
        if not password_hash:
            password = md5(password.encode()).hexdigest()
        self.password = password

    @classmethod
    def get_user_from_basic_auth(cls, auth_info):
        auth_info_decode = b64decode(auth_info).decode("utf-8")
        name_pass = auth_info_decode.split(":")
        if len(name_pass) != 2:
            return None
        return cls(name_pass[0], name_pass[1], password_hash=True)

    def is_username_exist(self):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE username='{username}';".format(username=self.username))
            amount = cur.fetchone()[0]

        if amount >= 1:
            return True
        return False

    def is_user_exist(self):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE username='{username}' and password='{password}'".format(
                username=self.username,
                password=self.password,
            ))
            user_id = cur.fetchone()
            if user_id is None:
                self.pk, self.is_new = None, True
            else:
                self.pk, self.is_new = user_id[0], False
        return self.is_new

    def get_credentials(self):
        return b64encode("{}:{}".format(self.username, self.password).encode("utf-8")).decode(
                    "utf-8")

    def save(self):
        conn = get_db()
        with conn.cursor() as cur:
            if self.is_new:
                cur.execute(
                    "INSERT INTO users(username, password) VALUES ('{username}', '{password}') RETURNING user_id;".format \
                        (username=self.username,
                         password=self.password))
                self.pk = cur.fetchone()[0]
            else:
                cur.execute("UPDATE users SET username='{username}', password='{password}' WHERE user_id={pk};".format \
                                (username=self.username,
                                 password=self.password,
                                 pk=self.pk))
        conn.commit()
        self.is_new = False
