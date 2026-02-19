"""
==========================================================
THE HISTORICAL COURT - A4 REPORT EDITION
Multi-Agent System using Google ADK
==========================================================

Architecture:
Root (Inquiry)
  -> Sequential (court_process)
      -> Loop (trial_loop)
          -> Parallel (investigation)
              - admirer (Defense)
              - critic (Prosecution)
          -> judge (must call exit_loop)
      -> verdict_writer (A4 body I–VI)
      -> sentencing_agent (VII–VIII intl law)
      -> file_writer (compose A4 layout + save)

Design Rules:
- Strict state separation: topic, pos_data, neg_data, verdict,
  verdict_body, sentencing_body
- Loop termination MUST use exit_loop only
- Anti-hallucination: explicitly restrict allowed tools
- Defensive MODEL fallback
==========================================================
"""

# ==========================================================
# IMPORTS
# ==========================================================

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


# ==========================================================
# ENVIRONMENT SAFETY
# ==========================================================

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"
MODEL_NAME = os.getenv("MODEL")

if not MODEL_NAME or not isinstance(MODEL_NAME, str):
    logging.warning(f"MODEL not set. Falling back to: {DEFAULT_MODEL}")
    MODEL_NAME = DEFAULT_MODEL

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, attempts=6)

# Cloud logging (safe to init even in Cloud Shell)
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

logging.info(f"Historical Court initialized with model: {MODEL_NAME}")


# ==========================================================
# TOOLS (STATE + FILE)
# ==========================================================

def append_to_state(tool_context: ToolContext, field: str, content: str):
    """
    Append content into a list-based state field.
    Ensures accumulation across loop iterations.
    """
    existing = tool_context.state.get(field, [])
    if not isinstance(existing, list):
        existing = [existing]
    tool_context.state[field] = existing + [content]
    logging.info(f"[STATE UPDATE] {field} length = {len(tool_context.state[field])}")
    return {"status": "success"}


def set_state(tool_context: ToolContext, field: str, content: str):
    """
    Set single-value state (e.g., topic, verdict).
    """
    if not isinstance(content, str):
        raise TypeError(f"{field} must be string.")
    tool_context.state[field] = content
    logging.info(f"[STATE SET] {field}")
    return {"status": "success"}


def write_file(tool_context: ToolContext, directory: str, filename: str, content: str):
    """
    Persist final report to disk.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"[FILE WRITTEN] {path}")
    return {"status": "success"}


# ==========================================================
# WIKIPEDIA TOOL
# ==========================================================

wikipedia_tool = LangchainTool(
    tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
)


# ==========================================================
# INVESTIGATION (PARALLEL)
# ==========================================================

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


# ==========================================================
# JUDGE LOOP (MUST CALL exit_loop)
# ==========================================================

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


# ==========================================================
# VERDICT WRITER (A4 BODY I–VI)
# ==========================================================

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


# ==========================================================
# SENTENCING (VII–VIII INTERNATIONAL LAW)
# ==========================================================

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


# ==========================================================
# FILE WRITER (A4 LAYOUT COMPOSER)
# ==========================================================

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


# ==========================================================
# ORCHESTRATION
# ==========================================================

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


# ==========================================================
# ROOT AGENT (ENTRY)
# ==========================================================

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
