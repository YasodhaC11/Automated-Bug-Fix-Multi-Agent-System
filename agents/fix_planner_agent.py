import json
import os
from state import AgentState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
from tools import clean_json_response, log_trace, run_tests


def fix_planner_agent(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""
        You are a senior Python debugging expert.

        Using all the evidence below, analyze the bug and return a JSON with:
        - "root_cause": clear explanation of why the bug occurs
        - "confidence": one of [high, medium, low]
        - "fix_plan": list of concrete steps to fix the issue
        - "patch": minimal corrected Python code that fixes the bug
        - "files_impacted": list of files/modules that need changes
        - "risks": potential risks or side effects of the fix
        - "verification": list of steps to verify the fix works
        - "open_questions": list of things still unknown or unclear
        - "test_code": a complete pytest test function that verifies the fix works.
                       Must be valid standalone Python. Use only standard library or pytest.

        Respond ONLY with valid JSON. No extra text.

        Issue Summary     : {state["issue_summary"]}
        Error Type        : {state["error_type"]}
        Reproduction Code : {state["reproduction_code"]}
        Repro Result      : {state.get("repro_result", "Not available")}
        Log Evidence      : {state.get("evidence", "No evidence available")}
        """
    try:
        response = llm.invoke(prompt)
        parsed = json.loads(clean_json_response(response.content))

        state["root_cause"] = f"{parsed.get('root_cause', 'N/A')} (Confidence: {parsed.get('confidence', 'unknown')})"
        state["fix_plan"] = json.dumps(parsed.get("fix_plan", []), indent=2)
        state["patch"] = parsed.get("patch", "")
        state["files_impacted"] = json.dumps(parsed.get("files_impacted", []), indent=2)
        state["risks"] = parsed.get("risks", "")
        state["verification"] = json.dumps(parsed.get("verification", []), indent=2)
        state["open_questions"] = json.dumps(parsed.get("open_questions", []), indent=2)

        # Save and run generated test
        test_code = parsed.get("test_code", "")
        if test_code:
            os.makedirs("output", exist_ok=True)
            with open("output/test_fix.py", "w", encoding="utf-8") as f:
                f.write(test_code)
            print("  [FIX_PLANNER] Running generated test...")
            test_result = run_tests("output/test_fix.py")
            state["test_result"] = test_result
            print(f"  [FIX_PLANNER] Test result: {test_result[:120]}")
        else:
            state["test_result"] = "No test generated"
        ####

        log_trace("fix_planner_agent", "llm_invoke",
                  str(state.get("issue_summary") or "")[:50],
                  str(state.get("root_cause") or "")[:100])

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        state["root_cause"] = "Fix planner failed: invalid JSON"
        state["test_result"] = "No test — JSON parse error"
    except Exception as e:
        print(f"Fix planner error: {e}")
        state["root_cause"] = f"Fix planner failed: {str(e)}"
        state["test_result"] = "No test — agent error"

    return state


if __name__ == "__main__":
    state = {
        "bug_report": "",
        "logs": "",
        "issue_summary": "Application crashes when dividing by zero",
        "error_type": "ZeroDivisionError",
        "reproduction_code": "a = 1\nb = 0\nc = a / b",
        "repro_result": "CONFIRMED: ZeroDivisionError reproduced.\nZeroDivisionError: division by zero",
        "evidence": json.dumps({
            "stack_trace": ["ZeroDivisionError: division by zero"],
            "anomalies": ["User request received: calculate(10, 0)"],
            "summary": "ZeroDivisionError when dividing 10 by 0"
        }, indent=2),
        "root_cause": None,
        "fix_plan": None,
        "patch": None,
        "files_impacted": None,
        "risks": None,
        "verification": None,
        "open_questions": None,
        "test_result": None
    }

    result = fix_planner_agent(state)

    print("\n=== FIX PLANNER RESULTS ===")
    print("Root Cause    :", result["root_cause"])
    print("\nFix Plan      :\n", result["fix_plan"])
    print("\nPatch         :\n", result["patch"])
    print("\nFiles Impacted:\n", result["files_impacted"])
    print("\nRisks         :", result["risks"])
    print("\nVerification  :\n", result["verification"])
    print("\nOpen Questions:\n", result["open_questions"])
    print("\nTest Result   :\n", result["test_result"])