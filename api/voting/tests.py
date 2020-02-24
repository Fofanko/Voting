import unittest
from api.base_tests import BaseTestCase
import json
from api.auth.models import User
from .models import Answer, Voting, Vote
from api.db import get_db


class AnswerTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        with self.app.app_context():
            self.user.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        self.voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            self.voting.save()

    def test_change_answer(self):
        """
            Change answer No to No! by id
        """
        id_answer_for_change = 1
        answer_no = list(filter(lambda answer: answer.pk == id_answer_for_change, self.voting.answers))[0]
        answer_no.answer = "No!"
        with self.app.app_context():
            answer_no.save(self.voting.pk)
            db_answer = Answer.get_answer_by_id(self.voting.pk, id_answer_for_change)
        self.assertEqual(answer_no.answer, db_answer.answer)

    def test_get_answer_out_of_range(self):
        with self.app.app_context():
            db_answer = Answer.get_answer_by_num(self.voting.pk, 100)
        self.assertEqual(db_answer, None)

    def test_count_of_votes(self):
        for_the_nth_answer = [2, 3]
        for idx, answer in enumerate(self.voting.answers):
            for _ in range(for_the_nth_answer[idx]):
                with self.app.app_context():
                    Vote(self.user.pk, answer.pk).save()
        with self.app.app_context():
            self.assertEqual(self.voting.answers[0].get_count_of_votes(), 2)
            self.assertEqual(self.voting.answers[1].get_count_of_votes(), 3)


class VotingTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        with self.app.app_context():
            self.user.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}

    def test_create_voting(self):
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            voting.save()
            db_voting = Voting.get_voting_by_id(voting.pk)
        self.assertEqual(db_voting.question, voting.question)

    def test_count_of_all_votes(self):
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            voting.save()
        for_the_nth_answer = [2, 3]
        for id, answer in enumerate(voting.answers):
            for _ in range(for_the_nth_answer[id]):
                with self.app.app_context():
                    Vote(self.user.pk, answer.pk).save()
        with self.app.app_context():
            all_votes_count = voting.get_all_votes_count()
        self.assertEqual(sum(for_the_nth_answer), all_votes_count)

    def test_count_of_answers(self):
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            voting.save()
            answers_count = Voting.get_count_of_answers_by_id(voting.pk)
        self.assertEqual(2, answers_count)


class VoteTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        with self.app.app_context():
            self.user.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        self.voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            self.voting.save()

    def test_vote_create(self):
        answer_num = 1
        with self.app.app_context():
            answer = Answer.get_answer_by_num(self.voting.pk, answer_num)
        vote = Vote(self.user.pk, answer.pk)
        with self.app.app_context():
            vote.save()
            db_vote = Vote.get_users_vote(self.user.pk, self.voting.pk)
        self.assertEqual(db_vote.pk, vote.pk)

    def test_change_vote(self):
        answer_num = 2
        new_answer_num = 1
        with self.app.app_context():
            answer = Answer.get_answer_by_num(self.voting.pk, answer_num)
        vote = Vote(self.user.pk, answer.pk)
        with self.app.app_context():
            vote.save()
            new_answer = Answer.get_answer_by_num(self.voting.pk, new_answer_num)
            vote.answer_id = new_answer.pk
            vote.save()
            db_vote = Vote.get_users_vote(self.user.pk, self.voting.pk)
        self.assertEqual(db_vote.answer_id, vote.answer_id)


class VotingListAPITestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        with self.app.app_context():
            self.user.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}

    def test_auth(self):
        response = self.client.get('/voting_list', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)

    def test_get_empty_list(self):
        response = self.client.get('/voting_list', headers=self.auth_header)
        response_data = json.loads(response.data.decode('utf8'))
        right_data = {"success": True,
                      "data": {
                          "votings": [

                          ]
                      },
                      "error_msg": None}
        self.assertEqual(response_data, right_data)

    def test_get_list(self):
        first_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        second_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "What day is it today?",
            "answers": ["Monday", "Tuesday", "Wednesday"]
        }).data.decode("utf8"))["data"]["id"]
        response = self.client.get('/voting_list', headers=self.auth_header)
        response_data = json.loads(response.data.decode('utf8'))
        right_data = {"success": True,
                      "data": {
                          "votings": [
                              {
                                  "id": first_id,
                                  "question": "It's a good weather today?",
                              },
                              {
                                  "id": second_id,
                                  "question": "What day is it today?"
                              }
                          ]
                      },
                      "error_msg": None}
        self.assertEqual(response_data, right_data)


class VotingAPITestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        with self.app.app_context():
            self.user.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}

    def test_create_voting(self):
        response_data = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))
        self.assertEqual(True, response_data["success"])

    def test_create_voting_with_one_answer(self):
        response_data = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes"]
        }).data.decode("utf8"))
        right_data = {
            "success": False,
            "data": {},
            "error_msg": "Minimum 2 Answers"
        }
        self.assertEqual(right_data, response_data)

    def test_check_voting(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        response_data = json.loads(self.client.get('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "Yes"
                    },
                    {
                        "answer_number": 2,
                        "answer": "No"
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_create_voting_with_same_answer_eventually_two(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No", "No"]
        }).data.decode("utf8"))["data"]["id"]
        response_data = json.loads(self.client.get('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = [
            {
                "answer_number": 1,
                "answer": "Yes"
            },
            {
                "answer_number": 2,
                "answer": "No"
            }
        ]
        self.assertCountEqual(right_data, response_data["data"]["answers"])

    def test_create_voting_with_same_answer_eventually_one(self):
        response_data = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "Yes"]
        }).data.decode("utf8"))
        right_data = {
            "success": False,
            "data": {},
            "error_msg": "Minimum 2 Answers"
        }
        self.assertCountEqual(right_data, response_data)

    def test_update_voting(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        self.client.put('/voting/{}'.format(voting_id),
                        headers=self.auth_header, data={
                "question": "It's a good weather today???",
                "answers": ["Yes", "No!"]
            }).data.decode("utf8")
        response_data = json.loads(self.client.get('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today???",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "Yes"
                    },
                    {
                        "answer_number": 2,
                        "answer": "No!"
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_update_voting_change_all_answer(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        self.client.put('/voting/{}'.format(voting_id),
                        headers=self.auth_header, data={
                "question": "It's a good weather today???",
                "answers": ["OK", "Not ok!"]
            }).data.decode("utf8")
        response_data = json.loads(self.client.get('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today???",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "OK"
                    },
                    {
                        "answer_number": 2,
                        "answer": "Not ok!"
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_update_voting_with_one_answer(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        response_data = json.loads(self.client.put('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header, data={
                "question": "It's a good weather today???",
                "answers": ["Ok"]
            }).data.decode("utf8"))
        right_data = {
            "success": False,
            "data": {},
            "error_msg": "Minimum 2 Answers"
        }
        self.assertEqual(right_data, response_data)

    def test_check_update_voting_with_one_answer(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        self.client.put('/voting/{}'.format(voting_id),
                        headers=self.auth_header, data={
                "question": "It's a good weather today???",
                "answers": ["Ok"]
            })
        response_data = json.loads(self.client.get('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "Yes"
                    },
                    {
                        "answer_number": 2,
                        "answer": "No"
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_delete_voting(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        response_data = json.loads(self.client.delete('/voting/{}'.format(voting_id),
                                                      headers=self.auth_header).data.decode("utf8"))
        self.assertEqual(True, response_data["success"])

    def test_check_delete_voting(self):
        voting_id = json.loads(self.client.post('/voting_list', headers=self.auth_header, data={
            "question": "It's a good weather today?",
            "answers": ["Yes", "No"]
        }).data.decode("utf8"))["data"]["id"]
        self.client.delete('/voting/{}'.format(voting_id), headers=self.auth_header).data.decode("utf8")
        response_data = json.loads(self.client.get('/voting/{}'.format(voting_id),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": False,
            "data": {},
            "error_msg": "Voting not found"
        }
        self.assertEqual(right_data, response_data)


class VoteAPITestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        with self.app.app_context():
            self.user.save()
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        self.voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            self.voting.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}

    def test_get_vote(self):
        response_data = json.loads(self.client.post('/vote/{}'.format(self.voting.pk),
                                                    headers=self.auth_header, data={
                "answer_number": 1,
            }).data.decode("utf8"))
        self.assertEqual(True, response_data["success"])

    def test_check_vote(self):
        self.client.post('/vote/{}'.format(self.voting.pk),
                         headers=self.auth_header, data={
                "answer_number": 1,
            })
        response_data = json.loads(self.client.get('/voting/{}'.format(self.voting.pk),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "Yes",
                        "percent": 100.0,
                        "your_replay": True
                    },
                    {
                        "answer_number": 2,
                        "answer": "No",
                        "percent": 0.0,
                        "your_replay": False
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_delete_vote(self):
        self.client.delete('/vote/{}'.format(self.voting.pk),
                           headers=self.auth_header)
        response_data = json.loads(self.client.get('/voting/{}'.format(self.voting.pk),
                                                   headers=self.auth_header).data.decode("utf8"))
        self.assertEqual(True, response_data["success"])

    def test_check_delete(self):
        self.client.post('/vote/{}'.format(self.voting.pk),
                         headers=self.auth_header, data={
                "answer_number": 1,
            })
        self.client.delete('/vote/{}'.format(self.voting.pk),
                           headers=self.auth_header)
        response_data = json.loads(self.client.get('/voting/{}'.format(self.voting.pk),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "Yes",
                    },
                    {
                        "answer_number": 2,
                        "answer": "No",
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_get_another_answer(self):
        self.client.post('/vote/{}'.format(self.voting.pk),
                         headers=self.auth_header, data={
                "answer_number": 1,
            })
        self.client.put('/vote/{}'.format(self.voting.pk),
                        headers=self.auth_header, data={
                "answer_number": 2,
            })
        response_data = json.loads(self.client.get('/voting/{}'.format(self.voting.pk),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 2,
                        "answer": "No",
                        "percent": 100.0,
                        "your_replay": True
                    },
                    {
                        "answer_number": 1,
                        "answer": "Yes",
                        "percent": 0.0,
                        "your_replay": False
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_calculate_percent(self):
        users = []
        answers = [1, 2, 2, 2]
        for i in range(4):
            users.append(User("test_username_{}".format(i), "test_password_{}".format(i)))
        with self.app.app_context():
            for user, ans_num in zip(users, answers):
                user.save()
                self.client.post('/vote/{}'.format(self.voting.pk),
                                 headers={"WWW-Authenticate": user.get_credentials()}, data={
                        "answer_number": ans_num,
                    })
        response_data = json.loads(self.client.get('/voting/{}'.format(self.voting.pk),
                                                   headers={
                                                       "WWW-Authenticate": users[0].get_credentials()}).data.decode(
            "utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 2,
                        "answer": "No",
                        "percent": 75.0,
                        "your_replay": False
                    },
                    {
                        "answer_number": 1,
                        "answer": "Yes",
                        "percent": 25.0,
                        "your_replay": True
                    }

                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)


class AnswerAPITestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User("test_user", "test_password")
        answers = [
            Answer("Yes"),
            Answer("No")
        ]
        with self.app.app_context():
            self.user.save()
        self.voting = Voting(user_id=self.user.pk, question="It's a good weather today?", answers=answers)
        with self.app.app_context():
            self.voting.save()
        self.answer_num = 1
        self.answer = self.voting.answers[self.answer_num - 1]
        self.vote = Vote(self.user.pk, self.answer.pk)
        with self.app.app_context():
            self.vote.save()
        self.auth_header = {"WWW-Authenticate": self.user.get_credentials()}

    def test_change_answer(self):
        response_data = json.loads(self.client.put('/answer/{}/{}'.format(self.voting.pk, self.answer_num),
                                                   headers=self.auth_header, data={
                "answer": "Yes!",
            }).data.decode("utf8"))
        self.assertEqual(True, response_data["success"])

    def test_check_change_answer(self):
        self.client.put('/answer/{}/{}'.format(self.voting.pk, self.answer_num),
                        headers=self.auth_header, data={
                "answer": "Yes!",
            })
        response_data = json.loads(self.client.get('/voting/{}'.format(self.voting.pk),
                                                   headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": True,
            "data": {
                "question": "It's a good weather today?",
                "answers": [
                    {
                        "answer_number": 1,
                        "answer": "Yes!",
                    },
                    {
                        "answer_number": 2,
                        "answer": "No",
                    }
                ]
            },
            "error_msg": None
        }
        self.assertEqual(right_data, response_data)

    def test_delete_answer(self):
        response_data = json.loads(self.client.delete('/answer/{}/{}'.format(self.voting.pk, self.answer_num),
                                                      headers=self.auth_header).data.decode("utf8"))
        right_data = {
            "success": False,
            "data": {},
            "error_msg": "Minimum 2 Answers"
        }
        self.assertEqual(right_data, response_data)


if __name__ == '__main__':
    unittest.main()
