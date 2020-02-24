from api.utils import SecureResource
from .models import Voting, Answer, Vote, VotingList
from flask_restful import reqparse
from flask import g
from collections import OrderedDict


class VotingListAPI(SecureResource):

    def get(self):
        voting_list = VotingList()
        self.response["success"] = True
        self.response["data"] = {
            "votings": voting_list.votings
        }
        return self.response

    def post(self):
        """
            Create a new voting
        """
        parser = reqparse.RequestParser()
        parser.add_argument('question', type=str, help="Question is required", required=True)
        parser.add_argument('answers', type=str, help="Answers is required", action='append', required=True)
        args = parser.parse_args()
        question, answers = args['question'], list(OrderedDict.fromkeys(args['answers']))
        if len(answers) < 2:
            self.response["success"] = False
            self.response["error_msg"] = "Minimum 2 Answers"
            return self.response
        voting = Voting(g.user.pk, question, [Answer(ans) for ans in answers])
        voting.save()
        self.response["success"] = True
        self.response["data"] = {
            "id": voting.pk
        }
        return self.response


class VotingAPI(SecureResource):
    def get_voting(self, voting_id):
        voting = Voting.get_voting_by_id(voting_id)
        if voting is None:
            self.response["success"] = False
            self.response["error_msg"] = "Voting not found"
            return None
        return voting

    def get(self, voting_id):
        voting = self.get_voting(voting_id)
        if voting is None:
            return self.response
        user_vote = Vote.get_users_vote(g.user.pk, voting.pk)
        self.response["success"] = True
        self.response["data"]["question"] = voting.question
        if user_vote is None:
            self.response["data"]["answers"] = [
                {
                    "answer_number": idx + 1,
                    "answer": ans.answer
                } for idx, ans in enumerate(voting.answers)
            ]
        else:
            all_votes_count = voting.get_all_votes_count()
            self.response["data"]["answers"] = sorted([
                {
                    "answer_number": idx + 1,
                    "answer": ans.answer,
                    "percent": ans.get_count_of_votes() / all_votes_count * 100,
                    "your_replay": True if ans.pk == user_vote.answer_id else False
                } for idx, ans in enumerate(voting.answers)
            ], key=lambda answers: answers["percent"], reverse=True)
        return self.response

    def put(self, voting_id):
        parser = reqparse.RequestParser()
        parser.add_argument('question', type=str, help="Question is required", required=True)
        parser.add_argument('answers', type=str, help="Answer is required", action='append', required=True)
        args = parser.parse_args()

        voting = self.get_voting(voting_id)
        if voting is None:
            return self.response
        if voting.user_id != g.user.pk:
            self.response["success"] = False
            self.response["error_msg"] = "Your are not owner of this voting"
            return self.response

        question, answers = args['question'], list(OrderedDict.fromkeys(args['answers']))

        # check count of answer after remove all and add new
        old_answer = set([ans for ans in voting.answers])
        if len((set(answers) - old_answer) | (set(answers) & old_answer)) < 2:
            self.response["success"] = False
            self.response["error_msg"] = "Minimum 2 Answers"
            return self.response

        voting.question = question
        voting.replace_answers(answers)
        voting.save()
        self.response["success"] = True
        return self.response

    def delete(self, voting_id):
        voting = self.get_voting(voting_id)
        if voting is None:
            return self.response
        if voting.user_id != g.user.pk:
            self.response["success"] = False
            self.response["error_msg"] = "Your are not owner of this voting"
            return self.response

        voting.delete()
        self.response["success"] = True
        return self.response


class AnswerAPI(SecureResource):

    def get_answer(self, voting_id, answer_num):
        answer = Answer.get_answer_by_num(voting_id, answer_num)
        if answer is None:
            self.response["success"] = False
            self.response["error_msg"] = "Voting or answer is missing"
            return None

        if answer.get_owner_id() != g.user.pk:
            self.response["success"] = False
            self.response["error_msg"] = "Your are not owner of this voting"
            return None
        return answer

    def put(self, voting_id, answer_num):
        parser = reqparse.RequestParser()
        parser.add_argument('answer', type=str, help="Answer is required", required=True)
        new_answer = parser.parse_args()["answer"]

        answer = self.get_answer(voting_id, answer_num)
        if answer is None:
            return self.response
        voting = Voting.get_voting_by_id(voting_id)
        print(new_answer)
        print([ans.answer for ans in voting.answers])
        if new_answer in [ans.answer for ans in voting.answers]:
            self.response["success"] = False
            self.response["error_msg"] = "This answer already exist"
            return self.response

        answer.answer = new_answer
        answer.save(voting_id)

        self.response["success"] = True
        return self.response

    def delete(self, voting_id, answer_num):
        answer = self.get_answer(voting_id, answer_num)
        if answer is None:
            return self.response

        print(Voting.get_count_of_answers_by_id(voting_id) < 3)
        if Voting.get_count_of_answers_by_id(voting_id) < 3:
            self.response["success"] = False
            self.response["error_msg"] = "Minimum 2 Answers"
            return self.response

        answer.delete()
        self.response["success"] = True
        return self.response


class VoteAPI(SecureResource):

    def post(self, voting_id):
        """
            record answer
        """
        parser = reqparse.RequestParser()
        parser.add_argument('answer_number', type=int, help="Answer number is required", required=True)
        answer_num = parser.parse_args()["answer_number"]

        is_user_voted = False if Vote.get_users_vote(g.user.pk, voting_id) is None else True
        if is_user_voted:
            self.response["success"] = False
            self.response["error_msg"] = "You are already voted. Use PUT request for change vote."
            return self.response
        answer = Answer.get_answer_by_num(voting_id, answer_num)
        if answer is None:
            self.response["success"] = False
            self.response["error_msg"] = "Voting or answer with this number is missing"
            return self.response

        vote = Vote(g.user.pk, answer.pk)
        vote.save()
        self.response["success"] = True
        return self.response

    def put(self, voting_id):
        parser = reqparse.RequestParser()
        parser.add_argument('answer_number', type=int, help="Answer number is requires param", required=True)
        answer_num = parser.parse_args()["answer_number"]

        is_user_voted = False if Vote.get_users_vote(g.user.pk, voting_id) is None else True
        if not is_user_voted:
            self.response["success"] = False
            self.response["error_msg"] = "You are not voted. Use POST to vote."
            return self.response
        answer = Answer.get_answer_by_num(voting_id, answer_num)
        if answer is None:
            self.response["success"] = False
            self.response["error_msg"] = "Answer with this number is missing"
            return self.response

        vote = Vote.get_users_vote(g.user.pk, voting_id)

        vote.answer_id = answer.pk
        vote.save()
        self.response["success"] = True
        return self.response

    def delete(self, voting_id):
        vote = Vote.get_users_vote(g.user.pk, voting_id)
        if vote is None:
            self.response["success"] = False
            self.response["error_msg"] = "You are not voted yet"
            return self.response
        vote.delete()
        self.response["success"] = True
        return self.response
