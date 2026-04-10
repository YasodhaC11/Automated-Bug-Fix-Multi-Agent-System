import json
from state import AgentState
from tools import execute_code
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from tools import log_trace

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def critic_agent(state: AgentState) -> AgentState:

    # Re-execute repro to independently verify
    print("=== CRITIC: RE-EXECUTING REPRO SCRIPT ===")
    actual_error = execute_code(state["reproduction_code"])
    print("Actual Execution Output:", actual_error)
    log_trace("critic_agent", "execute_code",
              str(state.get("reproduction_code") or "")[:100],  # ← safe
              actual_error[:100])

    expected_error = state.get("error_type", "")
    match_status = "MATCH" if expected_error in actual_error else "MISMATCH"
    print(f"Error Match Status: {match_status}")

    prompt = f"""
    You are a senior software engineer performing a critical review of a debugging pipeline's outputs.
    
    Your job is to challenge assumptions, find weaknesses, and ensure correctness and safety.
    
    Return a JSON with:
    - "repro_quality": assessment of whether repro is correct and truly minimal
    - "is_truly_minimal": true or false — could the repro be even smaller?
    - "root_cause_valid": true or false — is the root cause accurate?
    - "weak_assumptions": list of assumptions that may be wrong or unverified
    - "fix_safety": is the proposed fix safe? any risks?
    - "fix_correct": true or false
    - "edge_cases": list of at least 3 edge cases the fix might not handle
    - "improvements": list of concrete suggestions to improve the fix or plan
    - "overall_verdict": one of [approved, needs_revision, rejected]
    - "verdict_reason": short explanation of the verdict
    
    Respond ONLY with valid JSON. No extra text.
    
    --- PIPELINE OUTPUTS TO REVIEW ---
    
    Expected Error Type : {expected_error}
    Actual Execution    : {actual_error}
    Error Match         : {match_status}

    Reproduction Code:{state["reproduction_code"]}
    Repro Result:{state.get("repro_result", "N/A")}
    Log Evidence:{state.get("evidence", "N/A")}
    Root Cause:{state["root_cause"]}
    Fix Plan:{state["fix_plan"]}
    Patch:{state.get("patch", "N/A")}
    Verification Plan:{state.get("verification", "N/A")}
    """
    try:
        response = llm.invoke(prompt)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])  # remove first line (```json)
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])  # remove last line (```)
        raw = raw.strip()

        parsed = json.loads(raw)

        state["critique"] = json.dumps({
            "repro_quality"     : parsed.get("repro_quality", ""),
            "is_truly_minimal"  : parsed.get("is_truly_minimal", False),
            "root_cause_valid"  : parsed.get("root_cause_valid", False),
            "weak_assumptions"  : parsed.get("weak_assumptions", []),
            "fix_safety"        : parsed.get("fix_safety", ""),
            "fix_correct"       : parsed.get("fix_correct", False),
            "edge_cases"        : parsed.get("edge_cases", []),
            "improvements"      : parsed.get("improvements", []),
            "overall_verdict"   : parsed.get("overall_verdict", "needs_revision"),
            "verdict_reason"    : parsed.get("verdict_reason", "")
        }, indent=2)
        log_trace("critic_agent", "llm_invoke",
                  "critique request",
                  str(state.get("critique") or "")[:100])

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        state["critique"] = "Critic failed: invalid JSON"
    except Exception as e:
        print(f"Critic error: {e}")
        state["critique"] = f"Critic failed: {str(e)}"

    return state


if __name__ == "__main__":

    state = {
        "bug_report": "",
        "logs": "",
        "issue_summary": "Application crashes when dividing by zero",
        "error_type": "ZeroDivisionError",
        "reproduction_code": "a = 1\nb = 0\nc = a / b",
        "repro_result": "CONFIRMED: ZeroDivisionError reproduced.",
        "evidence": '{"stack_trace": ["ZeroDivisionError: division by zero"]}',
        "root_cause": "No zero check before division. (Confidence: high)",
        "fix_plan": '["Add zero check", "Use try/except"]',
        "patch": "try:\n    c = a / b\nexcept ZeroDivisionError:\n    c = 'Error'",
        "verification": '["Test with b=0", "Test with b=1"]',
        "critique": None,
        "open_questions": None
    }

    result = critic_agent(state)

    print("\n=== CRITIC RESULTS ===")
    print(result["critique"])