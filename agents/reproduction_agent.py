import os
from state import AgentState
from tools import execute_code
from langchain_openai import ChatOpenAI
from tools import log_trace
from dotenv import load_dotenv
load_dotenv()

REPRO_FILE = "repro_script.py"

def reproduction_agent(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Step 1: Generate minimal repro script ---
    prompt = f"""
        You are a Python debugging assistant.
        Generate a minimal Python script that reproduces the bug described below.
        
        STRICT RULES:
        - Return ONLY valid Python code
        - Do NOT include ``` or markdown
        - Do NOT include the word 'python'
        - No explanations, no comments
        - The script must raise the exact error when run
        
        Issue  : {state["issue_summary"]}
        Error  : {state["error_type"]}
        Evidence from logs:
        {state.get("evidence", "No evidence available")}
        """
    try:
        response = llm.invoke(prompt)
        code = response.content.strip()

        # Strip markdown fences if LLM ignored rules
        if code.startswith("```"):
            code = "\n".join(code.split("\n")[1:-1]).strip()

        state["reproduction_code"] = code
        print("=== GENERATED REPRO CODE ===")
        print(code)

        # Step 2: Save to file
        with open(REPRO_FILE, "w") as f:
            f.write(code)
        print(f"\nRepro script saved to: {REPRO_FILE}")
        log_trace("reproduction_agent", "save_repro_file",
                  "repro_script.py",
                  "file saved")
        # Step 3: Execute the script
        print("\n=== EXECUTING REPRO SCRIPT ===")
        repro_result = execute_code(code)
        state["repro_result"] = repro_result
        print("Execution Output:", repro_result)
        log_trace("reproduction_agent", "execute_code",
                  str(state.get("reproduction_code") or "")[:100],  # ← safe
                  repro_result[:100])
        # Step 4: Verify error matches log evidence
        expected_error = state.get("error_type", "")
        if expected_error and expected_error in repro_result:
            print(f"\n✅Confirmed: '{expected_error}' reproduced successfully")
            state["repro_result"] = f"CONFIRMED: {expected_error} reproduced.\n{repro_result}"
        elif repro_result == "NoError":
            print("\n⚠️ Warning: Script ran without error — repro may be incomplete")
            state["repro_result"] = f"WARNING: No error raised. Script may need revision.\n{repro_result}"
        else:
            print(f"\n⚠️ Different error than expected: {repro_result}")
            state["repro_result"] = f"MISMATCH: Expected {expected_error}, got:\n{repro_result}"

    except Exception as e:
        print(f"Reproduction agent error: {e}")
        state["repro_result"] = f"Reproduction failed: {str(e)}"

    return state


if __name__ == "__main__":

    state = {
        "bug_report": "",
        "logs": "",
        "issue_summary": "Application crashes when dividing by zero",
        "error_type": "ZeroDivisionError",
        "evidence": '{"stack_trace": ["ZeroDivisionError: division by zero"], "summary": "Division by zero error"}',
        "reproduction_code": None,
        "repro_result": None,
        "root_cause": None,
        "fix_plan": None,
        "verification": None
    }

    result = reproduction_agent(state)

    print("\n=== REPRODUCTION RESULTS ===")
    print("Code:\n", result["reproduction_code"])
    print("\nResult:", result["repro_result"])