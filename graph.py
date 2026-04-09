import json
import os
import datetime
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from state import AgentState

from agents.triage_agent       import triage_agent
from agents.log_analyst_agent  import log_analyst_agent
from agents.reproduction_agent import reproduction_agent
from agents.fix_planner_agent  import fix_planner_agent
from agents.reviewer_agent     import critic_agent

# ── Conditional routing ────────────────────────────────────────────────────
def should_retry(state: AgentState) -> str:
    try:
        critique = json.loads(state.get("critique", "{}"))
        verdict  = critique.get("overall_verdict", "approved")
        retry    = state.get("retry_count") or 0

        print(f"\n  [DEBUG] verdict={verdict}, retry_count={retry}")

        if verdict == "needs_revision" and retry < 2:
            print(f"\n🔁 Verdict: NEEDS_REVISION — retrying Fix Planner (attempt {retry}/2)")
            return "retry"
        else:
            print(f"\n✅ Verdict: {verdict.upper()} — pipeline complete after {retry} attempt(s)")
            return "done"
    except Exception as e:
        print(f"should_retry error: {e}")
        return "done"

# ── Wrapped agents with retry counter ─────────────────────────────────────
def fix_planner_with_retry(state: AgentState) -> AgentState:
    result = fix_planner_agent(state)
    # Explicitly carry over AND increment retry_count
    current = state.get("retry_count") or 0
    result["retry_count"] = current + 1
    print(f"  [DEBUG] retry_count set to: {result['retry_count']}")
    return result

# ── Build the graph ────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("triage",       triage_agent)
    graph.add_node("log_analyst",  log_analyst_agent)
    graph.add_node("reproduction", reproduction_agent)
    graph.add_node("fix_planner",  fix_planner_with_retry)
    graph.add_node("critic",       critic_agent)

    graph.set_entry_point("triage")
    graph.add_edge("triage",       "log_analyst")
    graph.add_edge("log_analyst",  "reproduction")
    graph.add_edge("reproduction", "fix_planner")
    graph.add_edge("fix_planner",  "critic")

    # Conditional edge: retry or finish
    graph.add_conditional_edges(
        "critic",
        should_retry,
        {
            "retry" : "fix_planner",
            "done"  : END
        }
    )

    return graph.compile()


# ── Save final JSON output ─────────────────────────────────────────────────
def save_output(state: AgentState, path: str = "output.json"):
    output = {
        "bug_summary": {
            "symptoms"  : state.get("issue_summary", "N/A"),
            "error_type": state.get("error_type",    "N/A"),
            "severity"  : state.get("severity",      "N/A"),
            "scope"     : "calculator.py - divide function"
        },
        "evidence"    : state.get("evidence", "N/A"),
        "repro": {
            "steps"    : "Run repro_script.py",
            "artifact" : "repro_script.py",
            "command"  : "python repro_script.py",
            "code"     : state.get("reproduction_code", "N/A"),
            "result"   : state.get("repro_result",      "N/A")
        },
        "root_cause_hypothesis": {
            "hypothesis": state.get("root_cause", "N/A"),
            "confidence": "high"
        },
        "patch_plan": {
            "fix_plan"      : state.get("fix_plan",       "N/A"),
            "patch"         : state.get("patch",          "N/A"),
            "files_impacted": state.get("files_impacted", "N/A"),
            "risks"         : state.get("risks",          "N/A")
        },
        "validation_plan": {
            "verification"  : state.get("verification",   "N/A"),
            "open_questions": state.get("open_questions", "N/A")
        },
        "critique"    : state.get("critique", "N/A"),
        "retry_count" : state.get("retry_count", 0)
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Final output saved to: {path}")
    return output


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    # Clear previous traces
    with open("traces.log", "w", encoding="utf-8") as f:
        f.write("")
    print("🗑️  traces.log cleared\n")

    with open(os.path.join("sample_inputs", "bug_report.md"), "r", encoding="utf-8") as f:
        bug_report = f.read()
    with open(os.path.join("sample_inputs", "app.log"), "r", encoding="utf-8") as f:
        logs = f.read()

    initial_state: AgentState = {
        "bug_report"       : bug_report,
        "logs"             : logs,
        "issue_summary"    : None,
        "error_type"       : None,
        "severity"         : None,
        "evidence"         : None,
        "reproduction_code": None,
        "repro_result"     : None,
        "root_cause"       : None,
        "fix_plan"         : None,
        "patch"            : None,
        "files_impacted"   : None,
        "risks"            : None,
        "verification"     : None,
        "open_questions"   : None,
        "critique"         : None,
        "retry_count"      : 0
    }

    print("=" * 60)
    print("   BUG FIX MULTI-AGENT PIPELINE STARTING")
    print("=" * 60)

    app = build_graph()
    final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("   PIPELINE COMPLETE — SUMMARY")
    print("=" * 60)
    print(f"Issue    : {final_state.get('issue_summary', 'N/A')}")
    print(f"Error    : {final_state.get('error_type',    'N/A')}")
    print(f"Severity : {final_state.get('severity',      'N/A')}")
    print(f"Cause    : {final_state.get('root_cause',    'N/A')}")
    print(f"Retries  : {final_state.get('retry_count',   0)}")

    try:
        critique = json.loads(final_state.get("critique", "{}"))
        print(f"Verdict  : {critique.get('overall_verdict', 'N/A').upper()}")
    except:
        print("Verdict  : N/A")

    save_output(final_state)


if __name__ == "__main__":
    main()