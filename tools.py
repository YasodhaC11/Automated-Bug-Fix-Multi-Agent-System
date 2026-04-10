import subprocess
import tempfile
import os
import re

# 1. extract_error_type
def extract_error_type(logs: str) -> str:
    """
    Extract the actual error type from logs.
    Returns the match (real error, not noise).
    """
    error_type = "UnknownError"
    for line in logs.split("\n"):
        line = line.strip()
        if "Error" in line or "Exception" in line:
            candidate = line.split(":")[0].strip()
            if " " not in candidate and candidate:
                error_type = candidate
    return error_type


# 2. grep_search
def grep_search(text: str, keyword: str) -> list:
    """
    Search for lines containing a keyword (case-insensitive).
    Returns matched lines with line numbers.
    """
    results = []
    for i, line in enumerate(text.split("\n"), 1):
        if keyword.lower() in line.lower():
            results.append(f"L{i}: {line.strip()}")
    return results


# 3. execute_code
def execute_code(code: str) -> str:
    """
    Executes Python code safely via subprocess.
    Returns full stdout + stderr output.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else "NoOutput"

    except subprocess.TimeoutExpired:
        return "TimeoutError: code execution exceeded 10 seconds"
    except FileNotFoundError:
        return "ExecutionError: Python interpreter not found"
    except Exception as e:
        return f"ExecutionError: {str(e)}"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# 4. run_tests
def run_tests(test_path: str = ".") -> str:
    """
    Runs pytest on the given path.
    Returns full test output.
    """
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else "No test output"
    except subprocess.TimeoutExpired:
        return "TimeoutError: tests exceeded 30 seconds"
    except Exception as e:
        return f"Error running tests: {str(e)}"


# 5. extract_stack_trace
def extract_stack_trace(logs: str) -> str:
    """
    Extracts full stack trace block from logs.
    """
    lines = logs.split("\n")
    trace_lines = []
    capturing = False

    for line in lines:
        if "Traceback" in line:
            capturing = True
            trace_lines = [line]
        elif capturing:
            trace_lines.append(line)
            # Stop after the actual error line (e.g. ZeroDivisionError: ...)
            if re.match(r"^\w+Error:|^\w+Exception:", line.strip()):
                break

    return "\n".join(trace_lines).strip() if trace_lines else "No stack trace found"


# 6. save_repro_file
def save_repro_file(code: str, path: str = "repro_script.py") -> str:
    """
    Saves reproduction code to a file.
    Returns the file path.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return path
    except Exception as e:
        return f"Error saving file: {str(e)}"

def clean_json_response(text: str) -> str:
    """
    Strips markdown code fences from LLM JSON responses.
    Handles ```json ... ``` and ``` ... ```
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        text = "\n".join(lines[1:-1]).strip()
    return text

import datetime
import json

def log_trace(agent: str, tool: str, inp: str, out: str):
    """
    Logs agent decisions and tool calls to traces.log
    """
    trace = {
        "timestamp" : datetime.datetime.now().isoformat(),
        "agent"     : agent,
        "tool"      : tool,
        "input"     : inp[:200],
        "output"    : out[:200]
    }
    with open("traces.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(trace) + "\n")
    print(f"   [{agent}] → {tool}")

# Quick self-test
if __name__ == "__main__":
    logs = """
INFO 2024-01-10 10:00:01 Server started on port 8080
DEBUG 2024-01-10 10:00:05 Memory usage: 45MB
WARNING 2024-01-10 10:00:12 Deprecated API endpoint called
Traceback (most recent call last):
  File "calculator.py", line 5, in <module>
    result = divide(10, 0)
  File "calculator.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero
INFO 2024-01-10 10:00:13 Connection pool size: 10
"""

    print("=== extract_error_type ===")
    print(extract_error_type(logs))

    print("\n=== grep_search: Error ===")
    print(grep_search(logs, "Error"))

    print("\n=== grep_search: WARNING ===")
    print(grep_search(logs, "WARNING"))

    print("\n=== execute_code ===")
    print(execute_code("a = 1\nb = 0\nc = a / b"))

    print("\n=== extract_stack_trace ===")
    print(extract_stack_trace(logs))

    print("\n=== save_repro_file ===")
    print(save_repro_file("a = 1\nb = 0\nc = a / b"))

    print("\n=== run_tests ===")
    print(run_tests("."))