# 🐛 Bug Fix Multi-Agent Pipeline
### Purple Merit Technologies — Assessment 2

An automated multi-agent system that ingests a bug report and logs, reproduces the issue, and outputs a root-cause hypothesis, patch plan, and optional patch — orchestrated using **LangGraph** and **OpenAI GPT-4o-mini**.

---

## 📁 Project Structure

```
purplemerit-bugfix-agent/
├── sample_inputs/
│   ├── bug_report.md          # Input: bug report (Markdown)
│   └── app.log                # Input: application logs with noise
├── agents/
│   ├── __init__.py
│   ├── triage_agent.py        # Extracts symptoms, severity, hypotheses
│   ├── log_analyst_agent.py   # Parses logs, extracts stack trace & anomalies
│   ├── reproduction_agent.py  # Generates & executes minimal repro script
│   ├── fix_planner_agent.py   # Proposes root cause, patch, verification plan
│   └── reviewer_agent.py      # Critic: challenges assumptions, suggests edge cases
├── state.py                   # Shared AgentState (TypedDict)
├── tools.py                   # Tool functions used by agents
├── graph.py                   # LangGraph orchestrator (entry point)
├── repro_script.py            # Auto-generated reproduction artifact
├── output.json                # Auto-generated structured final output
├── traces.log                 # Agent decision & tool call trace log
├── .env                       # API keys (not committed)
├── requirements.txt
└── README.md
```

---

## 🧠 Input Mode

**Option A — Provided Mini-Repo** (with intentionally introduced bug)

| File | Description |
|---|---|
| `data/bug_report.md` | Bug title, description, expected vs actual behavior, reproduction hints |
| `data/app.log` | Stack trace + noise lines (INFO, DEBUG, WARNING) to test log robustness |

The bug is a `ZeroDivisionError` in a `divide()` function with no zero-check — a classic missing guard condition.

---

## 🤖 Agent Roles

### 1. Triage Agent
Reads the bug report and extracts structured information via LLM:
- Issue summary, expected vs actual behavior
- Error type, severity (`critical / high / medium / low`)
- Environment details
- Ranked hypotheses of possible causes

### 2. Log Analyst Agent
Combines tool-based grep search with LLM reasoning:
- Uses `grep_search()` to find Error/Exception/Traceback/Warning lines
- Uses `extract_stack_trace()` to isolate the full trace block
- LLM identifies signal vs noise, anomalies, frequency, and summary

### 3. Reproduction Agent
Generates and executes a minimal failing script:
- LLM generates the smallest possible Python script that reproduces the bug
- `execute_code()` runs it via subprocess (safe, no `exec()`)
- Verifies the error type matches log evidence
- Saves artifact to `repro_script.py`

### 4. Fix Planner Agent
Proposes a complete fix using all prior evidence:
- Root cause with confidence level
- Step-by-step fix plan
- Actual patch code
- Files impacted, risks, verification steps, open questions

### 5. Critic / Reviewer Agent
Independently re-executes the repro and challenges the fix:
- Checks if repro is truly minimal
- Validates root cause accuracy
- Identifies weak assumptions
- Proposes edge cases
- Returns verdict: `approved / needs_revision / rejected`

---

## 🔄 Pipeline Flow

```
[Triage Agent]
      ↓
[Log Analyst Agent]
      ↓
[Reproduction Agent]
      ↓
[Fix Planner Agent] ←────────────┐
      ↓                          │ retry (max 2x)
[Critic Agent] ── needs_revision ┘
      ↓
   approved
      ↓
   [END] → output.json
```

The graph uses a **conditional edge** after the Critic Agent:
- If verdict is `needs_revision` and retries < 2 → loops back to Fix Planner
- Otherwise → pipeline ends and saves output

---

## 🛠️ Tools (`tools.py`)

| Tool | Used By | Description |
|---|---|---|
| `extract_error_type(logs)` | Log Analyst | Extracts error class name from logs |
| `grep_search(text, keyword)` | Log Analyst | Case-insensitive line search with line numbers |
| `execute_code(code)` | Reproduction, Critic | Runs Python code safely via subprocess, returns full traceback |
| `extract_stack_trace(logs)` | Log Analyst | Isolates full stack trace block from logs |
| `save_repro_file(code, path)` | Reproduction | Saves generated repro script to disk |
| `run_tests(path)` | Optional | Runs pytest on a given path, returns output |
| `clean_json_response(text)` | All agents | Strips markdown fences from LLM JSON responses |

---

## ⚙️ Setup & Installation

### 1. Clone the repo
```bash
git clone <repo-url>
cd purplemerit-bugfix-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-your-key-here
```

### 4. Run the pipeline
```bash
python graph.py
```

---

## 📦 Requirements

```
langchain-openai
langgraph
python-dotenv
pytest
```

Install with:
```bash
pip install langchain-openai langgraph python-dotenv pytest
```

**Runtime:** Python 3.10+

---

## 📤 Outputs

### `repro_script.py` — Reproduction Artifact
Auto-generated minimal Python script that consistently reproduces the bug.

**How to run:**
```bash
python repro_script.py
```

**Expected failing output:**
```
Traceback (most recent call last):
  File "repro_script.py", line 4, in <module>
    result = divide(10, 0)
  File "repro_script.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero
```

### `output.json` — Structured Final Report
Contains all required fields:

```json
{
  "bug_summary":            { "symptoms", "error_type", "severity", "scope" },
  "evidence":               { "stack_trace", "anomalies", "noise", "frequency", "summary" },
  "repro":                  { "steps", "artifact", "command", "code", "result" },
  "root_cause_hypothesis":  { "hypothesis", "confidence" },
  "patch_plan":             { "fix_plan", "patch", "files_impacted", "risks" },
  "validation_plan":        { "verification", "open_questions" },
  "critique":               { "verdict", "edge_cases", "improvements", "weak_assumptions" }
}
```

---

## 🔍 Traces & Traceability

**Location:** `traces.log` (project root)

Each line is a JSON entry recording agent decisions and tool calls:

```json
{
  "timestamp": "2024-01-10T10:00:12.345678",
  "agent": "reproduction_agent",
  "tool": "execute_code",
  "input": "def divide(a, b):\n    return a / b ...",
  "output": "ZeroDivisionError: division by zero"
}
```

**How to read:**
- Each entry shows which agent called which tool, with input/output summaries
- Follow entries in timestamp order to trace the full reasoning chain
- Console output during `python graph.py` also shows live agent progress and raw LLM responses

**Console trace includes:**
- Raw LLM responses from each agent
- Tool execution outputs
- Critic verdict and retry decisions

---

## 🧪 Example Run Summary

```
============================================================
   BUG FIX MULTI-AGENT PIPELINE STARTING
============================================================

[1/5] Triage Agent        → ZeroDivisionError | severity: high
[2/5] Log Analyst Agent   → Stack trace extracted, 3 noise lines filtered
[3/5] Reproduction Agent  → repro_script.py confirmed ✅
[4/5] Fix Planner Agent   → Patch proposed (raise ValueError)
[5/5] Critic Agent        → needs_revision → retry → APPROVED ✅

============================================================
   PIPELINE COMPLETE
============================================================
Verdict  : APPROVED
Output   : output.json
```

---

## 📝 Design Decisions

**Why LangGraph?** Clean state machine model with explicit node handoffs and conditional edges — ideal for deterministic multi-agent pipelines.

**Why subprocess over `exec()`?** Security and accuracy — subprocess captures the full traceback from stderr, which `exec()` cannot do safely.

**Why JSON outputs from LLMs?** Structured, parseable, reliable — avoids brittle text parsing that breaks on minor LLM formatting changes.

**Why a retry loop?** The Critic acts as a quality gate. If the fix is weak, the pipeline self-corrects up to 2 times before forcing completion — mimicking a real code review cycle.