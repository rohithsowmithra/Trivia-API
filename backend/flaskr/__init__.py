import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random

from backend.models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):

  page = request.args.get('page', 1, type=int)

  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  app.config['SECRET_KEY'] = 'dev'
  app.config['CORS_HEADERS'] = 'Content-Type'
  
  '''
  Set up CORS. Allow '*' for origins.
  '''
  cors = CORS(app, resources={r"/.*": {"origins":"*"}})


  '''
  Use the after_request decorator to set Access-Control-Allow headers
  '''
  @app.after_request
  def after_request(response):

    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')

    return response


  '''
  Endpoint to GET all available categories.
  '''

  @app.route("/categories")
  def retrieve_categories():

    categories = Category.query.order_by(Category.type).all()

    if len(categories) == 0:
      abort(404)

    return jsonify({
      "success": True,
      "categories": {category.id : category.type for category in categories}
    })


  '''
  Endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint will return a list of questions, 
  number of total questions, current category, categories. 
  '''

  @app.route('/questions')
  def retrieve_questions():

    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)

    categories = Category.query.order_by(Category.id).all()

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": len(questions),
      "categories": {category.id: category.type for category in categories},
      "currentCategory": None
    })


  '''
  Endpoint to DELETE question using a question ID. 
  '''

  @app.route("/questions/<int:question_id>", methods=["DELETE"])
  def delete_question(question_id):

    try:
      question_obj = Question.query.filter(Question.id == question_id).one()
      print(question_obj.format())
      question_obj.delete()

      return jsonify({
        "success": True,
        "deleted": question_id
      })
    except:
      abort(422)


  '''
  Endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty level.
  '''

  @app.route("/questions", methods=["POST"])
  def add_question():

    body = request.get_json()

    if not ('question' in body and 'answer' in body and 'category' in body and 'difficulty' in body):
      abort(422)

    question_val = body.get('question')
    answer_val = body.get('answer')
    category_val = body.get('category')
    difficulty_val = body.get('difficulty')

    try:

      question_obj = Question(question_val, answer_val, category_val, difficulty_val)
      question_obj.insert()

      questions = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, questions)

      return jsonify({
        "success": True,
        "created": question_obj.id,
        "questions": current_questions,
        "total_questions": len(questions)
      })
    except:
      question_obj.rollback()
      abort(422)


  ''' 
  Endpoint to get questions based on a search term sent using POST body. 
  It returns one/more questions that matches the substring of the question.
  '''

  @app.route("/questions/search", methods=["POST"])
  def search_questions():

    body = request.get_json()
    search_term = body.get('searchTerm')

    if search_term:

      questions_obj = Question.query.filter(Question.question.ilike("%" + search_term + "%")).all()

      if not questions_obj:
        abort(404)

      current_questions = paginate_questions(request, questions_obj)

      return jsonify({
        "success": True,
        "questions": current_questions,
        "total_questions": len(questions_obj),
        "current_category": None
      })
    else:
      abort(404)


  '''
  GET endpoint to get questions based on category. 
  '''

  @app.route("/categories/<int:category_id>/questions", methods=["GET"])
  def retrieve_questions_by_category(category_id):

    try:

      category_ids = [cat.id for cat in Category.query.with_entities(Category.id, Category.type).order_by(Category.id).all()]

      if category_id not in category_ids:
        abort(404)

      questions_obj = Question.query.filter(Question.category == str(category_id)).all()
      current_questions = paginate_questions(request, questions_obj)


      return jsonify({
        "success": True,
        "questions": current_questions,
        "total_questions": len(questions_obj),
        "currentCategory": category_id
      })
    except:
      abort(404)



  '''
  POST endpoint to get questions to play the quiz. 
  This endpoint takes category and previous question parameters 
  and returns a random question within the given category, 
  if provided, and that is not one of the previous questions. 
  '''

  @app.route("/quizzes", methods=["POST"])
  def play_quiz():

    try:

      body = request.get_json()

      if not ('previous_questions' in body and 'quiz_category' in body):
        abort(422)

      previous_questions = body.get('previous_questions')
      quiz_category = body.get('quiz_category')

      if quiz_category['type'] == 'click':
        available_questions = Question.query.filter(Question.id.notin_((previous_questions))).all()
      else:
        available_questions = Question.query.filter(Question.category == quiz_category['id']).filter(Question.id.notin_((previous_questions))).all()

      question = available_questions[random.randrange(0, len(available_questions))].format() if len(available_questions) > 0 else None

      return jsonify({
        'success': True,
        'question': question
      })

    except:
      abort(422)

  '''
  Error handlers for all expected errors including 404 and 422. 
  '''

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request"
    }), 400

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

  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "messgae": "An internal error has occured"
    }), 500

  return app


if __name__ == "__main__":
  app = create_app()
  app.run(debug=True)