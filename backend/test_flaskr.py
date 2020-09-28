import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from backend.flaskr import create_app
from backend.models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.db_test_user = 'postgres'
        self.db_password = 'root'
        self.database_name = "trivia"
        self.database_path = "postgres://{}:{}@{}/{}".format(self.db_test_user, self.db_password,'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    Test cases for each successful operation and expected errors.
    """

    def test_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        total_questions = len(Question.query.all())

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_questions'], total_questions)
        self.assertTrue(data['questions'])
        self.assertTrue(data['categories'])


    def test_404_sent_requesting_questions_beyond_valid_page(self):
        res = self.client().get('/questions?page=100')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'resource not found')


    def test_get_categories(self):
        res  = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertTrue(len(data['categories']))


    def test_404_sent_requesting_invalid_category(self):
        res = self.client().get('/categories/10000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'resource not found')


    def test_delete_question(self):
        new_question = Question(question='TestQuestion', answer='TestAnswer', difficulty=1, category=1)
        new_question.insert()
        question_id = new_question.id

        res = self.client().delete('/questions/{}'.format(question_id))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)


    def test_422_sent_deleting_nonexisting_question(self):
        res = self.client().delete('/questions/{}'.format(12345))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')


    def test_add_new_question(self):
        new_question = {
            "question": "Question1",
            "answer": "Answer1",
            "difficulty": 1,
            "category": 1
        }

        question_before = len(Question.query.all())
        res = self.client().post('/questions', json=new_question)
        data = json.loads(res.data)
        questions_after = len(Question.query.all())

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])
        self.assertEqual(questions_after, question_before + 1)


    def test_422_sent_add_question_with_insufficient_data(self):
        new_question = {
            "question": "Question1",
            "answer": "Answer1",
            "difficulty": 1
        }

        question_before = len(Question.query.all())
        res = self.client().post('/questions', json=new_question)
        data = json.loads(res.data)
        questions_after = len(Question.query.all())

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')
        self.assertEqual(questions_after, question_before)


    def test_search_question(self):
        searchjson = {
            "searchTerm": "autobiography"
        }
        res = self.client().post('/questions/search', json=searchjson)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'], None)


    def test_404_sent_search_question(self):
        searchjson = {
            "searchTerm": ""
        }
        res = self.client().post('/questions/search', json=searchjson)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'resource not found')


    def test_retrieve_questions_by_category(self):
        category_id = 1
        res = self.client().get('/categories/{}/questions'.format(category_id))
        data = json.loads(res.data)

        print(data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['questions'])
        self.assertEqual(data['currentCategory'], category_id)


    def test_404_sent_retrieve_questions_by_category(self):
        category_id = 10000
        res = self.client().get('/categories/{}/questions'.format(category_id))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'resource not found')


    def test_play_quiz(self):
        playjson = {
            "previous_questions": [2, 4, 6],
            "quiz_category": {
                "type": "click",
                "id": 0
            }
        }
        res = self.client().post('/quizzes', json=playjson)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question']['id'])


    def test_422_sent_play_quiz(self):
        playjson = {
            "previous_questions": []
        }
        res = self.client().post('/quizzes', json=playjson)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()