from typing import TypedDict, Optional

class AgentState(TypedDict):
    # Inputs
    bug_report:     str
    logs:           str

    # Triage Agent
    issue_summary:  Optional[str]
    error_type:     Optional[str]
    severity:       Optional[str]

    # Log Analyst Agent
    evidence:       Optional[str]

    # Reproduction Agent
    reproduction_code: Optional[str]
    repro_result:      Optional[str]

    # Fix Planner Agent
    root_cause:        Optional[str]
    fix_plan:          Optional[str]
    patch:             Optional[str]
    files_impacted:    Optional[str]
    risks:             Optional[str]
    verification:      Optional[str]
    open_questions:    Optional[str]
    retry_count:       Optional[int]
    test_result:       Optional[str]
    # Critic Agent
    critique:          Optional[str]