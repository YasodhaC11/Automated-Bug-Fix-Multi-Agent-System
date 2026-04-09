import json
from state import AgentState
from tools import extract_error_type, grep_search, clean_json_response, log_trace
from langchain_openai import ChatOpenAI

def log_analyst_agent(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    logs = state["logs"]

    error_lines     = grep_search(logs, "Error")
    exception_lines = grep_search(logs, "Exception")
    traceback_lines = grep_search(logs, "Traceback")
    warning_lines   = grep_search(logs, "Warning")

    all_evidence = list(set(
        error_lines + exception_lines + traceback_lines + warning_lines
    ))

    # ← NO log_trace here, evidence not set yet

    extracted_error_type = extract_error_type(logs)
    state["error_type"] = extracted_error_type
    state["evidence"] = "\n".join(all_evidence) if all_evidence else "No evidence found"

    prompt = f"""
You are an expert log analyst for a software debugging pipeline.

Analyze the logs below and return a JSON with:
- "error_type": the specific error class (e.g. ZeroDivisionError)
- "stack_trace": the relevant stack trace lines only
- "anomalies": list of unusual or suspicious lines
- "noise": list of lines that are irrelevant / red herrings
- "frequency": how many times the error appears
- "summary": 2-3 sentence explanation of what the logs reveal

Respond ONLY with valid JSON. No extra text.

Logs:
{logs}

Pre-extracted evidence:
{state["evidence"]}
"""
    try:
        response = llm.invoke(prompt)
        print("RAW LLM RESPONSE:", response.content)
        parsed = json.loads(clean_json_response(response.content))

        state["error_type"] = parsed.get("error_type", extracted_error_type)
        state["evidence"] = json.dumps({
            "stack_trace" : parsed.get("stack_trace", []),
            "anomalies"   : parsed.get("anomalies", []),
            "noise"       : parsed.get("noise", []),
            "frequency"   : parsed.get("frequency", 1),
            "summary"     : parsed.get("summary", "")
        }, indent=2)

        # ✅ log_trace AFTER evidence is set
        log_trace("log_analyst_agent", "grep_search",
                  "keyword: Error/Exception/Traceback",
                  str(state.get("evidence") or "")[:100])

        log_trace("log_analyst_agent", "llm_invoke",
                  "logs analysis",
                  str(state.get("error_type") or ""))

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
    except Exception as e:
        print(f"Log analyst error: {e}")

    return state