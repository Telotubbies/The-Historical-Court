"""
The Historical Court — Multi-Agent International Tribunal Simulation.

Google ADK-based system that evaluates historical figures/events through
a structured adversarial investigation, judicial review loop, and formal
legal report generation.

Architecture (ADK composition):
    root (inquiry) → court_process (SequentialAgent)
        → trial_loop (LoopAgent)
            → investigation (ParallelAgent) → admirer, critic
            → judge (must call exit_loop)
        → verdict_writer → sentencing_agent → file_writer

State keys (immutable contract): topic, pos_data, neg_data, verdict,
verdict_body, sentencing_body. Each agent writes only to its assigned key(s)
to prevent cross-agent contamination.

Loop control: ADK LoopAgent does not auto-terminate. The judge agent MUST
invoke exit_loop when evidence is sufficient; otherwise the loop continues
until max_iterations (6).
"""

import os
import logging
from datetime import datetime

import google.cloud.logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools import exit_loop
from google.adk.models import Gemini

from google.genai import types
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"
MODEL_NAME = os.getenv("MODEL")
if not MODEL_NAME or not isinstance(MODEL_NAME, str):
    logging.warning(f"MODEL not set. Falling back to: {DEFAULT_MODEL}")
    MODEL_NAME = DEFAULT_MODEL

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, attempts=6)
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()
logging.info(f"Historical Court initialized with model: {MODEL_NAME}")


# -----------------------------------------------------------------------------
# Tools + State Management Strategy
# State keys are the contract. Each agent writes only to assigned keys:
#   topic (inquiry), pos_data/neg_data (admirer/critic), verdict (judge),
#   verdict_body (verdict_writer), sentencing_body (sentencing_agent).
# Separation prevents cross-agent contamination (e.g. critic overwriting pos_data).
# -----------------------------------------------------------------------------

def append_to_state(tool_context: ToolContext, field: str, content: str):
    """
    Append content to a list-based state field.

    Ensures accumulation across loop iterations. Used by admirer (pos_data),
    critic (neg_data), and judge (verdict). Normalizes non-list existing
    values to list before concatenation.
    """
    existing = tool_context.state.get(field, [])
    if not isinstance(existing, list):
        existing = [existing]
    tool_context.state[field] = existing + [content]
    logging.info(f"[STATE UPDATE] {field} length = {len(tool_context.state[field])}")
    return {"status": "success"}


def set_state(tool_context: ToolContext, field: str, content: str):
    """
    Set a single-value state field. Used by inquiry agent for 'topic'.
    Validates content is str to avoid type corruption.
    """
    if not isinstance(content, str):
        raise TypeError(f"{field} must be string.")
    tool_context.state[field] = content
    logging.info(f"[STATE SET] {field}")
    return {"status": "success"}


def write_file(tool_context: ToolContext, directory: str, filename: str, content: str):
    """
    Persist final A4 report to disk. Creates directory if missing.
    Called only by file_writer after verdict and sentencing are composed.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"[FILE WRITTEN] {path}")
    return {"status": "success"}


wikipedia_tool = LangchainTool(
    tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
)


# -----------------------------------------------------------------------------
# ParallelAgent: investigation
# Runs admirer and critic concurrently. Each has isolated tools; admirer
# writes to pos_data, critic to neg_data. Parallelism ensures neither side
# sees the other's output before completing—improves evidence fairness and
# prevents implicit bias from sequential ordering.
# Anti-hallucination: admirer/critic have tools=[wikipedia_tool, append_to_state]
# only; no transfer_to_agent. Instruction forbids delegation. Restricts model
# to grounded actions.
# -----------------------------------------------------------------------------

admirer = Agent(
    name="admirer",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    description="Defense attorney collecting positive evidence.",
    instruction="""
ROLE: Defense Attorney

TOPIC:
{ topic? }

STRICT RULES:
- You can ONLY use tools: wikipedia, append_to_state
- Do NOT call transfer_to_agent
- Do NOT delegate
- If unsure about tools, continue reasoning without calling any other tool

TASK:
- Search using keywords: achievements, legacy, reforms,
  contributions, innovation, humanitarian efforts.
- Provide concise bullet points (max 5 per iteration).
- Store findings in 'pos_data' using append_to_state.
""",
    tools=[wikipedia_tool, append_to_state],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)

critic = Agent(
    name="critic",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    description="Prosecutor collecting negative evidence.",
    instruction="""
ROLE: Prosecutor

TOPIC:
{ topic? }

STRICT RULES:
- You can ONLY use tools: wikipedia, append_to_state
- Do NOT call transfer_to_agent
- Do NOT delegate

TASK:
- Search using keywords: controversy, war crimes,
  oppression, human rights violations, scandals.
- Provide concise bullet points (max 5 per iteration).
- Store findings in 'neg_data' using append_to_state.
""",
    tools=[wikipedia_tool, append_to_state],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)

investigation = ParallelAgent(
    name="investigation",
    description="Parallel prosecution and defense research.",
    sub_agents=[admirer, critic],
)


# -----------------------------------------------------------------------------
# LoopAgent: trial_loop + exit_loop enforcement
# LoopAgent runs [investigation, judge] until judge calls exit_loop.
# ADK does not infer termination from natural language; the loop continues
# until exit_loop is invoked or max_iterations (6) is reached.
# Mandatory exit_loop: prevents infinite loops and ensures explicit
# control transfer to verdict_writer. Judge instruction explicitly forbids
# "ending naturally" for this reason.
# -----------------------------------------------------------------------------

judge = Agent(
    name="judge",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    description="Ensures balanced evidence before verdict.",
    instruction="""
POSITIVE EVIDENCE:
{ pos_data? }

NEGATIVE EVIDENCE:
{ neg_data? }

RULES:
1. If either side has fewer than 3 substantial findings,
   order deeper research for that side.
2. If imbalance ratio > 2:1, strengthen weaker side.
3. If sufficient and reasonably balanced:
   - Write a neutral legal analysis.
   - Store it in 'verdict' using append_to_state.
   - MUST call exit_loop tool to terminate the loop.

IMPORTANT:
- You MUST use exit_loop.
- Do NOT end naturally.
""",
    tools=[append_to_state, exit_loop],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)

trial_loop = LoopAgent(
    name="trial_loop",
    description="Judicial review loop.",
    sub_agents=[investigation, judge],
    max_iterations=6,
)


# -----------------------------------------------------------------------------
# Verdict writer: A4 body sections I–VI. Reads topic, pos_data, neg_data, verdict.
# output_key="verdict_body" — ADK injects model output into state under this key.
# -----------------------------------------------------------------------------

verdict_writer = Agent(
    name="verdict_writer",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    output_key="verdict_body",
    instruction="""
ROLE: Chief Justice

TOPIC:
{ topic? }

POSITIVE:
{ pos_data? }

NEGATIVE:
{ neg_data? }

ANALYSIS:
{ verdict? }

Draft a formal court opinion in academic legal tone.

Structure EXACTLY:

I. BACKGROUND
II. ISSUES FOR DETERMINATION
III. FINDINGS OF FACT (POSITIVE)
IV. FINDINGS OF FACT (NEGATIVE)
V. LEGAL ANALYSIS
VI. VERDICT

Use full paragraph format.
Do NOT introduce new facts.
Maintain neutrality.
""",
    generate_content_config=types.GenerateContentConfig(temperature=0),
)


# -----------------------------------------------------------------------------
# Sentencing agent: International law layer (VII–VIII).
# Applies Rome Statute, Geneva Conventions, retroactivity principles.
# output_key="sentencing_body" — distinct from verdict_body for modular composition.
# -----------------------------------------------------------------------------

sentencing_agent = Agent(
    name="sentencing_agent",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    output_key="sentencing_body",
    instruction="""
ROLE: International Criminal Law Panel

TOPIC:
{ topic? }

NEGATIVE FINDINGS:
{ neg_data? }

VERDICT ANALYSIS:
{ verdict? }

Draft two sections:

VII. INTERNATIONAL LEGAL QUALIFICATION
VIII. HYPOTHETICAL SENTENCING OUTCOME

Evaluate under:
- Rome Statute (ICC)
- Geneva Conventions
- Crimes Against Humanity
- War Crimes
- Jurisdiction and retroactivity principles

If legal threshold not met, state clearly that no
prosecutable international crime would likely be established.

Maintain professional international tribunal tone.
""",
    generate_content_config=types.GenerateContentConfig(temperature=0),
)


# -----------------------------------------------------------------------------
# File writer: Composes final A4 layout from verdict_body and sentencing_body.
# Uses write_file tool; no model output written to state.
# -----------------------------------------------------------------------------

file_writer = Agent(
    name="file_writer",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    tools=[write_file],
    instruction=f"""
TOPIC:
{{ topic? }}

VERDICT BODY:
{{ verdict_body? }}

SENTENCING BODY:
{{ sentencing_body? }}

TASK:
Compose a formal A4-style report exactly as follows:

------------------------------------------------------------
                     THE HISTORICAL COURT
               INTERNATIONAL TRIBUNAL DIVISION
------------------------------------------------------------

Case Title: <TOPIC>
Docket No.: HC-2026-001
Date: {datetime.now().strftime("%d %B %Y")}

------------------------------------------------------------

<Insert Verdict Body Here>

<Insert Sentencing Body Here>

------------------------------------------------------------
Prepared by:
The Historical Court Simulation Engine
------------------------------------------------------------

Save file to:
directory = historical_reports
filename = <TOPIC>_Court_Report.txt
""",
    generate_content_config=types.GenerateContentConfig(temperature=0),
)


# -----------------------------------------------------------------------------
# SequentialAgent: court_process
# Enforces strict execution order: trial_loop → verdict_writer → sentencing_agent
# → file_writer. Each sub-agent runs only after the previous completes. Required
# because verdict_body and sentencing_body depend on trial_loop output (pos_data,
# neg_data, verdict). Violating order would cause downstream agents to read
# incomplete state.
# -----------------------------------------------------------------------------

court_process = SequentialAgent(
    name="court_process",
    description="Complete judicial workflow.",
    sub_agents=[
        trial_loop,
        verdict_writer,
        sentencing_agent,
        file_writer,
    ],
)


# -----------------------------------------------------------------------------
# Root agent: inquiry. Entry point; collects topic via set_state, then
# transfers to court_process. Uses sub_agents (not transfer_to_agent) for
# declarative routing.
# -----------------------------------------------------------------------------

root_agent = Agent(
    name="inquiry",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    description="Initiates Historical Court simulation.",
    instruction="""
Ask the user to provide a historical figure or event.
Store it in state key 'topic' using set_state tool.
Then transfer control to court_process.
""",
    tools=[set_state],
    sub_agents=[court_process],
    generate_content_config=types.GenerateContentConfig(temperature=0),
)
