from flask import Blueprint, request, jsonify
import sys, os
import json

# Step 1: Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Step 2: Import service
from services.github_services import get_file, add_file, update_file

# Step 3: Blueprint declaration
problems_bp = Blueprint("problems", __name__)

# Step 4: Flask route function
@problems_bp.route('/', methods=['GET'])
def get_problems():
    file_obj = get_file('data/problem_list.json')[0]
    if not file_obj:
        return jsonify({
            "message": f"file data/problem_list.json not found"
        })
    problems_json = json.loads(file_obj)
    return problems_json

@problems_bp.route('/<id>', methods=['GET'])
def get_problem(id):
    file_obj = get_file(f'data/problems/{id}/problem.json')[0]
    if not file_obj:
        return jsonify({
            "message": f"Problem with id {id} not found"
        })
    problem_json = json.loads(file_obj)
    return problem_json

@problems_bp.route('/add_problem', methods=['POST'])
def add_problem():
    pass
    # data = request.get_json()
    # id = data["id"]
    # file_path = f'data/problems/{id}/problem.json'
    # file_content = json.dumps(data, indent=2)
    # commit_message = f"Added problem {id}"
    # add_file(file_path, file_content, commit_message, 1)
    # return {"message": "Problem added"}

@problems_bp.route('/update_problem', methods=['POST'])
def update_problem():
    pass
    # data = request.get_json()
    # id = data["id"]
    # file_path = f'data/problems/{id}/problem.json'
    # file_content = json.dumps(data, indent=2)
    # commit_message = f"Updated problem {id}"
    # update_file(file_path, file_content, commit_message, 1)
    # return {"message": "Problem updated"}