from flask import Flask

from flask_restful import Api
from api.auth.resource import Registration
from api.voting.resource import VotingListAPI, VotingAPI, VoteAPI, AnswerAPI
import psycopg2.pool
import os


def create_app(test_config=False):
    app = Flask(__name__)
    if not test_config:
        app.config['postgreSQL_pool'] = psycopg2.pool.SimpleConnectionPool(1, 5,
                                                                           user="liis",
                                                                           host="127.0.0.1",
                                                                           port="5432",
                                                                           database="liis")
    else:
        app.config['postgreSQL_pool'] = psycopg2.pool.SimpleConnectionPool(1, 5,
                                                                           user="liis",
                                                                           host="127.0.0.1",
                                                                           port="5432",
                                                                           database="liis_test")
    api = Api(app)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .db import init_app

    db.init_app(app)

    api.add_resource(Registration, '/registration')
    api.add_resource(VotingListAPI, "/voting_list")
    api.add_resource(VotingAPI, "/voting/<int:voting_id>")
    api.add_resource(AnswerAPI, "/answer/<int:voting_id>/<int:answer_num>")
    api.add_resource(VoteAPI, "/vote/<int:voting_id>")

    return app
