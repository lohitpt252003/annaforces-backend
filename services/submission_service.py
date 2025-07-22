import os, time, json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from judge.judge import handle_submission_judge


def handle_submission(data):
    
    verdict = handle_submission_judge(data)
    return verdict
