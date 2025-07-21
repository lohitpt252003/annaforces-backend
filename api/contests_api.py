from flask import Blueprint, request, jsonify
import sys, os
import json

# Step 1: Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Step 2: Import service
from services.github_services import get_file, add_file, update_file

# Step 3: Blueprint declaration
contests_bp = Blueprint("contests", __name__)

# Step 4: Flask route function
@contests_bp.route('/', methods=['GET'])
def get_contests():
    file_obj = get_file('data/contest_list.json')[0]
    if not file_obj:
        return jsonify({
            "message": f"file data/contest_list.json not found"
        })
    contests_json = json.loads(file_obj)
    return contests_json

@contests_bp.route('/<id>', methods=['GET'])
def get_contest(id):
    file_obj = get_file(f'data/contests/{id}/contest.json')[0]
    if not file_obj:
        return jsonify({
            "message": f"contest with id {id} not found"
        })
    contest_json = json.loads(file_obj)
    return contest_json

@contests_bp.route('/add_contest', methods=['POST'])
def add_contest():
    pass
    # data = request.get_json()
    # id = data["id"]
    # file_path = f'data/contests/{id}/contest.json'
    # file_content = json.dumps(data, indent=2)
    # commit_message = f"Added contest {id}"
    # add_file(file_path, file_content, commit_message, 1)
    # return {"message": "contest added"}

@contests_bp.route('/update_contest', methods=['POST'])
def update_contest():
    pass
    # data = request.get_json()
    # id = data["id"]
    # file_path = f'data/contests/{id}/contest.json'
    # file_content = json.dumps(data, indent=2)
    # commit_message = f"Updated contest {id}"
    # update_file(file_path, file_content, commit_message, 1)
    # return {"message": "contest updated"}