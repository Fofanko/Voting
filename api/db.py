from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = current_app.config['postgreSQL_pool'].getconn()
    return g.db


def close_conn(e=None):
    db = g.pop('db', e)
    if db is not None:
        current_app.config['postgreSQL_pool'].putconn(db)


def init_app(app):
    app.teardown_appcontext(close_conn)
