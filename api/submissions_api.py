from flask import Blueprint, request, jsonify
import sys, os
import json

# Step 1: Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.submission_service import handle_submission
from services.github_services import get_file, add_file, update_file


submission_bp = Blueprint("submissions", __name__)

def add_submission(logs, data):
    user_id = int(data.get('user_id', '0'))
    problem_id = int(data.get('problem_id', '0'))
    last_submission = int(get_file(f'data/problems/{problem_id}/submissions/last_submission.txt').strip())
    update_file(f'data/problems/{problem_id}/submissions/last_submission.txt', last_submission + 1, f'got the submission {last_submission + 1}')
    file_path = f'data/problems/{problem_id}/submissions/{last_submission + 1}.json'
    add_file(file_path, logs, f'got the submission {last_submission + 1} by the user {user_id}')


# Step 4: Flask route function
@submission_bp.route('/submit', methods=['POST'])
def submit_solution():
    data = request.json
    try:
        logs = handle_submission(data)
        add_submission(logs, data)
        return jsonify({"status": "success", "verdict": logs}), 200
    except Exception as e:
        add_submission(str(e), data)
        return jsonify({"status": "error", "message": str(e)}), 500