import os, time, json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from judge.judge import judge_submission


def handle_submission(data):
    problem_id = data["problem_id"]
    username = data["username"]
    lang = data["language"]
    code = data["code"]

    timestamp = int(time.time())
    path = f"data/submissions/{problem_id}"
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, f"{username}_{timestamp}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    verdict = judge_submission(file_path)
    return verdict
