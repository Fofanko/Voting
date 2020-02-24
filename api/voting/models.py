from api.db import get_db
from typing import Optional


class Answer:
    def __init__(self, answer: str, pk: int = None):
        self.answer = answer
        self.pk = pk

    @classmethod
    def get_answer_by_num(cls, voting_id: int, num: int):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT answer_id, answer FROM answers
                    WHERE voting_id={voting_id}
                    ORDER BY answers.answer_id 
                    OFFSET {num} LIMIT 1 ;""".format(
                    voting_id=voting_id,
                    num=num - 1
                ))
            result = cur.fetchone()
        if not result:
            return None
        return cls(result[1], result[0])

    @classmethod
    def get_answer_by_id(cls, voting_id: int, answer_id: int):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT answer_id, answer FROM answers WHERE answer_id={answer_id};".format(
                    answer_id=answer_id,
                ))
            result = cur.fetchone()
        if not result:
            return None
        return cls(result[1], result[0])

    def get_count_of_votes(self):
        if self.pk is None:
            return None
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT COUNT(*) FROM votes
                    JOIN answers ON votes.answer_id=answers.answer_id
                    WHERE answers.answer_id={pk};
                """.format(pk=self.pk)
            )
            count = cur.fetchone()
        if not count:
            return 0
        return count[0]

    def get_owner_id(self):
        if self.pk is None:
            return None
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT user_id FROM votings
                    JOIN answers ON votings.voting_id=answers.voting_id
                    WHERE answers.answer_id={pk};
                """.format(pk=self.pk)
            )
            owner_id = cur.fetchone()
        if not owner_id:
            return None
        return owner_id[0]

    def save(self, voting_id: int):
        conn = get_db()
        with conn.cursor() as cur:
            if self.pk is None:
                cur.execute(
                    "INSERT INTO answers(voting_id, answer) VALUES ({voting_id}, '{answer}') RETURNING answer_id;".format \
                        (voting_id=voting_id,
                         answer=self.answer))
                self.pk = cur.fetchone()[0]
            else:
                # Delete votes with got old text answer
                cur.execute(
                    "DELETE FROM votes WHERE answer_id={pk}".format \
                        (pk=self.pk))
                cur.execute("UPDATE answers SET answer='{answer}' WHERE answer_id={pk};".format \
                                (answer=self.answer,
                                 pk=self.pk))
        conn.commit()

    def delete(self):
        if self.pk is None:
            return None
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM votes WHERE answer_id={pk}".format \
                    (pk=self.pk))
            cur.execute(
                "DELETE FROM answers WHERE answer_id={pk}".format \
                    (pk=self.pk))
        conn.commit()


class Voting:
    def __init__(self, user_id: int, question: str, answers: list, pk: int = None):
        self.user_id = user_id
        self.question = question
        self.answers = answers
        self.pk = pk

    @classmethod
    def get_voting_by_id(cls, pk: int):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT user_id, question, answer_id, answer FROM votings 
                    JOIN answers ON votings.voting_id=answers.voting_id 
                    WHERE votings.voting_id={pk}
                    ORDER BY answer_id;
                """.format(
                    pk=pk))
            result = cur.fetchall()
        if not result:
            return None
        answers = []
        for answer in result:
            answers.append(Answer(answer[3], answer[2]))
        return cls(result[0][0], result[0][1], answers, pk)

    @classmethod
    def get_count_of_answers_by_id(cls, pk: int):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT COUNT(*) FROM answers
                    WHERE answers.voting_id={pk};
                """.format(pk=pk)
            )
            count = cur.fetchone()
        if not count:
            return 0
        return count[0]

    def get_all_votes_count(self) -> Optional[int]:
        if self.pk is None:
            return None
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT COUNT(*) FROM votes
                    JOIN answers ON votes.answer_id=answers.answer_id
                    JOIN votings ON votings.voting_id=answers.voting_id
                    WHERE votings.voting_id={pk};
                """.format(pk=self.pk)
            )
            count = cur.fetchone()
        if not count:
            return 0
        return count[0]

    def get_answer_by_name(self, answer: str) -> Optional[Answer]:
        """
            get exist answer by name or None
        """
        for ans in self.answers:
            if ans.answer == answer:
                return ans
        return None

    def replace_answers(self, answers: list, remove_old=True):
        new_answers = []
        # remember answers for deletion if remove_old
        deleted_answers = list(filter(lambda del_a: del_a.answer not in answers, self.answers)) if remove_old else []
        for answer in answers:
            cur_answer = self.get_answer_by_name(answer)
            if cur_answer:
                # if answer not exist add to new
                new_answers.append(cur_answer)
            else:
                # else create a new answer
                new_answer = Answer(answer)
                new_answer.save(self.pk)
                new_answers.append(new_answer)
        # delete old answer from db
        for del_ans in deleted_answers:
            del_ans.delete()
        # replace old answer to new
        self.answers = new_answers

    def save(self):
        conn = get_db()
        with conn.cursor() as cur:
            if self.pk is None:
                # First of all create voting, and take his pk
                # for answer's relationship
                cur.execute(
                    "INSERT INTO votings(user_id, question) VALUES ({user_id}, '{question}') RETURNING voting_id;".format(
                        user_id=self.user_id, question=self.question.replace("'", "''")))
                self.pk = cur.fetchone()[0]
                for answer in self.answers:
                    answer.save(self.pk)
            else:
                cur.execute(
                    "UPDATE votings SET question='{question}' WHERE voting_id={pk};".format(
                        question=self.question.replace("'", "''"),
                        pk=self.pk))
        conn.commit()

    def delete(self):
        if self.pk is None:
            return None
        conn = get_db()
        with conn.cursor() as cur:
            for ans in self.answers:
                ans.delete()
            cur.execute(
                "DELETE FROM votings WHERE voting_id={pk}".format \
                    (pk=self.pk))
        conn.commit()


class Vote:
    def __init__(self, user_id: int, answer_id: int, pk: int = None):
        self.user_id = user_id
        self.answer_id = answer_id
        self.pk = pk

    @classmethod
    def get_users_vote(cls, user_id: int, voting_id: int):
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT votes.vote_id, votes.answer_id FROM votings
                JOIN votes on votes.user_id={user_id}
                WHERE votings.voting_id={voting_id}
            """.format(user_id=user_id, voting_id=voting_id))
            result = cur.fetchone()
        if not result:
            return None
        return cls(user_id, result[1], result[0])

    def save(self):
        conn = get_db()
        with conn.cursor() as cur:
            if self.pk is None:
                cur.execute(
                    "INSERT INTO votes(answer_id, user_id) VALUES ({answer_id}, {user_id} ) RETURNING vote_id;".format(
                        answer_id=self.answer_id, user_id=self.user_id))
                self.pk = cur.fetchone()[0]
            else:
                cur.execute(
                    "UPDATE votes SET answer_id={answer_id} WHERE vote_id={pk};".format(
                        answer_id=self.answer_id,
                        pk=self.pk))
        conn.commit()

    def delete(self):
        if self.pk is None:
            return None
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM votes WHERE vote_id={pk}".format(pk=self.pk))
        conn.commit()


class VotingList:
    def __init__(self):
        self.votings = []
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT voting_id, question
                FROM votings
            """)
            result = cur.fetchall()
        for res in result:
            self.votings.append({
                "id": res[0],
                "question": res[1]
            })
