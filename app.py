import random

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from werkzeug.wrappers import response

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_data(request, given_data):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  formatted_data = [item.format() for item in given_data]
  return formatted_data[start:end]

def get_paginted_all_questions(request):
  questions = Question.query.order_by(Question.id).all()
  current_question = paginate_data(request, questions)

  if len(current_question) == 0:
    abort(404)
  
  return {
    'success': True,
    'questions': current_question,
    'total_questions': len(Question.query.all()),
  }

def get_categories_data():
  categories = Category.query.order_by(Category.id).all()
  current_categories = {}
  for category in categories:
    current_categories[category.id] = category.type

  return {
      'success': True,
      'categories': current_categories
  }

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)
  
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  @app.route('/categories')
  def retrieve_categories():
    """Create an endpoint to handle GET requests for all available categories."""
    return jsonify(get_categories_data())

  @app.route('/questions')
  def retrieve_questions():
    """
      Create an endpoint to handle GET requests for questions, including pagination (every 10 questions). This endpoint should return a list of questions, 
      number of total questions, current category, categories.
    """
    questions = get_paginted_all_questions(request)
    questions.update(get_categories_data())
    return jsonify(questions)

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    """
      Create an endpoint to DELETE question using a question ID. 
    """
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()
      response_data = get_paginted_all_questions(request)
      response_data.update({'success': True, 'deleted': question_id})

      return jsonify(response_data)

    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_question():
    """
      Create an endpoint to POST a new question, which will require the question and answer text, category, and difficulty score.
    """
    try:
      request_data = request.get_json()
      question = Question(**request_data)
      question.insert()

      response_data = get_paginted_all_questions(request)
      response_data.update({'success': True, 'created': question.id})

      return jsonify(response_data)
    except:
      abort(422)

  @app.route('/questions/search', methods=['POST'])
  def search_question():
    """
      Create a POST endpoint to get questions based on a search term. It should return any questions for whom the search term is a substring of the question. 
    """
    search = request.get_json().get('search')
    questions = Question.query.filter(Question.question.ilike(f'%{search}%')).all()
    formatted_books = [question.format() for question in questions]

    return jsonify({
        'success': True,
        'questions':formatted_books,
        'total_questions': len(formatted_books)
    })

  @app.route('/categories/<int:category_id>/questions')
  def retrieve_questions_for_category(category_id):
    """
      Create a GET endpoint to get questions based on category.
    """
    questions = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
    current_question = paginate_data(request, questions)

    if len(current_question) == 0:
      abort(404)
    
    return jsonify({
      'success': True,
      'questions': current_question,
      'total_questions': len(Question.query.all()),
      'current_category': Category.query.get(category_id).type
    })

  @app.route('/quizzes', methods=['POST'])
  def quiz_question():
    """
      Create a POST endpoint to get questions to play the quiz. 
      This endpoint should take category and previous question parameters and return a random questions within the given category, 
      if provided, and that is not one of the previous questions. 
    """
    try:
      request_data = request.get_json()
      previous_questions = request_data.get('previous_questions', [])
      quiz_category = request_data.get('quiz_category', {})

      questions = Question.query.filter(~Question.id.in_(previous_questions))
      if quiz_category.get('id'):
        questions = questions.filter(Question.category == quiz_category.get('id'))

      questions_count = questions.count()
      if questions_count:
        rand = random.randrange(0, questions_count)
        question = questions[rand]
        question = question.format()
      else:
        question = None

      return jsonify({
        'success': True,
        'question': question
      })

    except:
      abort(422)


  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
      }), 400

  @app.errorhandler(405)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 405,
      "message": "method not allowed"
      }), 405
  
  @app.errorhandler(Exception)
  def server_error(error):
    return jsonify({
      "success": False, 
      "error": 500,
      "message": "something went wrong"
      }), 500
  
  
  return app
