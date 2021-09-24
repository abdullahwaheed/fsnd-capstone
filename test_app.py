import random
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.wrappers import request

from app import create_app
from models import setup_db, Question, Category
from settings import DB_NAME, DB_HOST, DB_USER, DB_PASSWORD


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_path = 'postgresql://{}:{}@{}/{}_test'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
        
        self.new_question = {
            'question': 'What is this?',
            'answer': 'test',
            'category': 1,
            'difficulty': 5,
            'id': 99
        }
    
    def tearDown(self):
        """Executed after reach test"""
        question = Question.query.get(self.new_question.get('id'))
        if question:
            question.delete()
    
    # # Quiz questions Test
    def test_quiz_questions_with_category(self):
        categories = Category.query.all()
        rand = random.randrange(0, len(categories)) 
        category = categories[rand]
        request_data = {'previos_questions': [], 'quiz_category': {'id': category.id, 'type': category.type}}
        res = self.client().post(f'/quizzes', json=request_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['question'].get('category'), category.id)

    def test_quiz_questions_without_category(self):
        request_data = {'previos_questions': [], 'quiz_category': {'id': 0, 'type': 'click'}}
        res = self.client().post(f'/quizzes', json=request_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])
    
    def test_question_with_wrong_data(self):
        request_data = {'previos_questions': [], 'quiz_category': {'id': 'abc', 'type': 'click'}}
        res = self.client().post(f'/quizzes', json=request_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    # Questions for category Test
    def test_questions_for_category(self):
        categories = Category.query.all()
        rand = random.randrange(0, len(categories)) 
        category = categories[rand]
        res = self.client().get(f'/categories/{category.id}/questions')
        data = json.loads(res.data)

        questions_count = Question.query.filter(Question.category == category.id).count()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), questions_count)
        self.assertEqual(data['current_category'], category.type)
        self.assertTrue(data['total_questions'])
    
    def test_404_sent_requesting_beyond_valid_page_for_categories(self):
        res = self.client().get('/categories/1000/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    # Question List Test
    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(isinstance(data['categories'], dict))
    
    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000', json={'rating': 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    # All categories List Test
    def test_get_all_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertTrue(isinstance(data['categories'], dict))
    
    # Delete question
    def test_delete_question(self):
        question = Question(**self.new_question)
        question.insert()
        question_id = question.id

        res = self.client().delete(f'/questions/{question_id}')
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == question_id).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertEqual(question, None)
        
    def test_422_if_question_does_not_exist(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')
    
    # Create question

    def test_create_new_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])
        self.assertTrue(len(data['questions']))
    
    def test_405_if_question_creation_not_allowed(self):
        res = self.client().post('/questions/45', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'method not allowed')

    # Search question
    def test_get_question_search_with_results(self):
        res = self.client().post('/questions/search', json={'search': 'title'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), 2)
    
    def test_get_question_search_without_results(self):
        res = self.client().post('/questions/search', json={'search': 'anonymous'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_questions'], 0)
        self.assertEqual(len(data['questions']), 0)

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
