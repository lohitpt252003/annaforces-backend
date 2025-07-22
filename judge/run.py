# File: judge/run.py

import subprocess
import tempfile
import shutil
import os
import dotenv

dotenv.load_dotenv()

# The name/tag of your built Docker image
DOCKER_IMAGE = os.getenv("JUDGE_IMAGE", "my-judge-image:latest")

# 50 MiB size limit
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
    Compile & run `code` in the judge Docker container under a host-mounted temp dir.
    Enforces:
      - code and stdin each ≤ 50 MiB
      - container-side file-size ulimit of 50 MiB
    Returns dict with 'stdout' and 'stderr' (never raises).
    """
    # 0) Pre‑write size checks
    if len(code.encode()) > MAX_BYTES:
        return {"stdout": "", "stderr": "Source code too large (>50 MiB)"}
    if stdin and len(stdin.encode()) > MAX_BYTES:
        return {"stdout": "", "stderr": "Input too large (>50 MiB)"}

    cfg = LANG_CONFIG.get(language)
    if not cfg:
        return {"stdout": "", "stderr": f"Unsupported language: {language}"}

    # 1) Prepare host temp dir
    tmpdir = tempfile.mkdtemp(prefix="judge_")
    try:
        # Write source
        src_path = os.path.join(tmpdir, cfg["file"])
        with open(src_path, "w") as f:
            f.write(code)

        # Write stdin if provided
        if stdin is not None:
            in_path = os.path.join(tmpdir, "input.txt")
            with open(in_path, "w") as f:
                f.write(stdin)
        else:
            in_path = None

        # 2) Build command string to run inside container
        cmds = []
        if cfg["compile"]:
            cmds.append(f"{cfg['compile']} 2> compile.err")
        run_cmd = cfg["run"]
        if in_path:
            cmds.append(f"timeout {timelimit} {run_cmd} < input.txt 2> runtime.err | tee output.txt")
        else:
            cmds.append(f"timeout {timelimit} {run_cmd} 2> runtime.err | tee output.txt")
        inner_cmd = " && ".join(cmds) + " || true"

        # 3) Docker invocation with file‑size ulimit
        docker_cmd = [
            "docker", "run", "--rm",
            "--ulimit", f"fsize={MAX_BYTES // 512}",   # 50 MiB in 512‑byte blocks
            "-v", f"{tmpdir}:/judge",
            "-w", "/judge",
            DOCKER_IMAGE,
            "bash", "-c", inner_cmd
        ]

        proc = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True
        )

        # 4) Read results
        stderr = ""
        stdout = ""

        # Compile‑error?
        ce = os.path.join(tmpdir, "compile.err")
        if os.path.exists(ce) and os.path.getsize(ce) > 0:
            with open(ce) as f: stderr = f.read().strip()
            return {"stdout": "", "stderr": stderr}

        # Runtime‑error or TLE?
        re = os.path.join(tmpdir, "runtime.err")
        if os.path.exists(re) and os.path.getsize(re) > 0:
            with open(re) as f: stderr = f.read().strip()

        # Normal output
        outf = os.path.join(tmpdir, "output.txt")
        if os.path.exists(outf):
            with open(outf) as f: stdout = f.read()

        return {"stdout": stdout, "stderr": stderr}

    finally:
        shutil.rmtree(tmpdir)
