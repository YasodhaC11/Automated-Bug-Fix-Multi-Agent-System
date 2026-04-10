import json
from state import AgentState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from tools import clean_json_response
from tools import log_trace

def triage_agent(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
You are a senior software engineer doing bug triage.

Analyze the bug report and extract the following as JSON:
- "issue_summary": 2-3 line summary
- "expected_behavior": what should happen
- "actual_behavior": what actually happens  
- "error_type": specific error class if mentioned
- "severity": one of [critical, high, medium, low]
- "environment": language/runtime/OS if mentioned
- "hypotheses": list of 1-3 ranked failure causes

Respond ONLY with valid JSON. No extra text.

Bug Report:{state["bug_report"]}
"""
    try:
        response = llm.invoke(prompt)
        #print("RAW LLM RESPONSE:", response.content)
        parsed = json.loads(clean_json_response(response.content))

        state["issue_summary"] = parsed.get("issue_summary", "N/A")
        state["error_type"]    = parsed.get("error_type", "UnknownError")
        state["severity"]      = parsed.get("severity", "medium")

        log_trace("triage_agent", "llm_invoke",
                  state["bug_report"][:100],
                  state["issue_summary"][:100])

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        state["issue_summary"] = "Triage failed: invalid JSON response"
    except Exception as e:
        print(f"Triage error: {e}")
        state["issue_summary"] = f"Triage failed: {str(e)}"

    return state


if __name__ == "__main__":
    state = {
        "bug_report": "Application crashes when dividing by zero. Expected graceful handling but throws ZeroDivisionError.",
        "logs": "",
        "issue_summary": None,
        "error_type": None,
        "severity": None,
        "reproduction_code": None,
        "root_cause": None,
        "fix_plan": None,
        "verification": None
    }

    result = triage_agent(state)

    print("\n=== TRIAGE RESULTS ===")
    print("Summary  :", result["issue_summary"])
    print("Error    :", result["error_type"])
    print("Severity :", result["severity"])