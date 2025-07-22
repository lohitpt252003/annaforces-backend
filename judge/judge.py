# File: judge/judge.py

import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from judge.run import run
from services.github_services import get_file, add_file, update_file


def handle_submission_judge(data):
    """
    Returns a list of log objects for each testcase.
    Never raises—errors are captured in the 'stderr' field.
    """
    problem_id   = int(data.get("problem_id", "0"))
    language     = data.get("language", 'py')
    code         = data.get("code", "print('Welcome to ANNAFORCES!')\nprint('Please enter the correct code.')")
    time_limit   = data.get("time_limit", "1s")
    memory_limit = data.get("memory_limit", "1024MB")
    logs = []

    # 1) How many testcases?
    raw = get_file(f"data/problems/{problem_id}/testcases/no.txt")[0]
    try:
        tests = int(raw.strip())
    except:
        # Invalid testcase count
        return [{"testcase": None, "stdout": "", "stderr": f"Invalid testcase count: {raw}", "testcase_status": False}]

    # 2) Loop through each testcase
    for test in range(1, tests + 1):
        stdin  = get_file(f"data/problems/{problem_id}/testcases/{test}.in")[0]
        expect = get_file(f"data/problems/{problem_id}/testcases/{test}.out")[0]

        out = run(code, stdin, language, time_limit, memory_limit)
        # print(code)
        # print(out)

        passed = (out["stdout"].strip() == expect.strip())
        logs.append({
            "testcase":        test,
            "stdin":           stdin,
            "expected_stdout": expect,
            "stdout":          out["stdout"],
            "stderr":          out["stderr"],
            "testcase_status": passed
        })

        # If runtime error or TLE (no stdout), still include that test and continue
        # (don’t abort early unless you explicitly want to stop on first RE/TLE)
    return logs