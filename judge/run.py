# File: judge/run.py

import subprocess
import tempfile
import shutil
import os
import dotenv

dotenv.load_dotenv()

# The name/tag of your built Docker image
DOCKER_IMAGE = os.getenv("JUDGE_IMAGE", "my-judge-image:latest")

# 50 MiB size limit
MAX_BYTES = 50 * 1024 * 1024

# Map language to filename and container commands
LANG_CONFIG = {
    "c":   {"file": "submission.c",   "compile": "gcc submission.c -o submission",  "run": "./submission"},
    "cpp": {"file": "submission.cpp", "compile": "g++ submission.cpp -o submission", "run": "./submission"},
    "py":  {"file": "submission.py",  "compile": None,                               "run": "python3 submission.py"},
    "java":{"file": "Main.java",      "compile": "javac Main.java",               "run": "java Main"},
}

def run(code, stdin=None, language=None, timelimit="1s", memorylimit="1024MB"):
    """
    Compile & run `code` in Docker, enforcing host-side timeout.
    Returns dict with 'stdout' and 'stderr' (never raises).
    """
    # Pre-write size checks
    if len(code.encode()) > MAX_BYTES:
        return {"stdout": "", "stderr": "Source code too large (>50 MiB)"}
    if stdin and len(stdin.encode()) > MAX_BYTES:
        return {"stdout": "", "stderr": "Input too large (>50 MiB)"}

    cfg = LANG_CONFIG.get(language)
    if not cfg:
        return {"stdout": "", "stderr": f"Unsupported language: {language}"}

    # Parse time limit, e.g. "2s" → 2
    try:
        sec = int(timelimit.rstrip("s"))
    except:
        sec = 1

    # Prepare host temp dir
    tmpdir = tempfile.mkdtemp(prefix="judge_", dir='./')
    try:
        # Write source
        src = os.path.join(tmpdir, cfg["file"])
        with open(src, "w") as f:
            f.write(code)

        # Write stdin if present
        if stdin is not None:
            in_file = os.path.join(tmpdir, "input.txt")
            with open(in_file, "w") as f:
                f.write(stdin)
        else:
            in_file = None

        # Build the in-container shell command
        cmds = []
        if cfg["compile"]:
            # compile, redirect stderr
            cmds.append(f"{cfg['compile']} 2> compile.err")
        # run executable/script, redirect stderr, capture stdout
        if in_file:
            cmds.append(f"{cfg['run']} < input.txt 2> runtime.err | tee output.txt")
        else:
            cmds.append(f"{cfg['run']} 2> runtime.err | tee output.txt")
        inner_cmd = " && ".join(cmds)

        # Full docker command
        docker_cmd = [
            "docker", "run", "--rm",
            "--ulimit", f"fsize={MAX_BYTES // 512}",
            "-v", f"{tmpdir}:/judge",
            "-w", "/judge",
            DOCKER_IMAGE,
            "bash", "-lc", inner_cmd
        ]

        # Execute with host-side timeout
        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=sec + 1
            )
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Time Limit Exceeded"}

        # Read results
        stderr = ""
        stdout = ""

        # Compile error?
        ce = os.path.join(tmpdir, "compile.err")
        if os.path.exists(ce) and os.path.getsize(ce) > 0:
            stderr = open(ce).read().strip()
            return {"stdout": "", "stderr": stderr}

        # Runtime error?
        re = os.path.join(tmpdir, "runtime.err")
        if os.path.exists(re) and os.path.getsize(re) > 0:
            stderr = open(re).read().strip()

        # Normal output
        out = os.path.join(tmpdir, "output.txt")
        if os.path.exists(out):
            stdout = open(out).read()

        return {"stdout": stdout, "stderr": stderr}

    finally:
        shutil.rmtree(tmpdir)
