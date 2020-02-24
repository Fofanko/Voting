from api.db import get_db


def migrate_db():
    conn = get_db()
    create_table_raw_sqls = ["""
        CREATE TABLE "users" (
            user_id serial PRIMARY KEY,
            username VARCHAR (50) UNIQUE NOT NULL,
            password VARCHAR (255) NOT NULL
        );
    """,
                             """
        CREATE TABLE "votings" (
            voting_id serial PRIMARY KEY,
            user_id INTEGER REFERENCES "users" (user_id),
            question TEXT NOT NULL
        );
    """,
                             """
        CREATE TABLE "answers" (
            answer_id serial PRIMARY KEY,
            voting_id INTEGER REFERENCES "votings" (voting_id),
            answer TEXT NOT NULL
        );
    """,
                             """
        CREATE TABLE "votes" (
            vote_id serial PRIMARY KEY,
            answer_id INTEGER REFERENCES "answers" (answer_id),
            user_id INTEGER REFERENCES "users" (user_id)
        );
    """
                             ]
    with conn.cursor() as cur:
        for sql in create_table_raw_sqls:
            cur.execute(sql)
    conn.commit()


def clear_db():
    conn = get_db()
    drop_table_raw_sqls = [
        'DROP TABLE "users" CASCADE ;',
        'DROP TABLE "votings" CASCADE;',
        'DROP TABLE "answers" CASCADE;',
        'DROP TABLE "votes" CASCADE;',
    ]
    with conn.cursor() as cur:
        for sql in drop_table_raw_sqls:
            cur.execute(sql)
    conn.commit()
