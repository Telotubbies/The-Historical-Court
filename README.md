![The Historical Court Architecture](image/README/1771512342119.png)

# The Historical Court

The Historical Court is a deterministic multi-agent system built with Google ADK.  
It simulates an international tribunal to analyze a historical figure or event using adversarial investigation, judicial supervision, and structured legal reporting.

The system produces a formal A4-style legal opinion including international law qualification and hypothetical sentencing.

---

## 1. Project Objective

This project demonstrates:

- Multi-Agent architecture design
- Parallel adversarial evidence gathering
- Judicial supervision with controlled loop termination
- Structured legal reasoning output
- Deterministic execution (temperature = 0)

The goal is to evaluate historical topics in a balanced and reproducible manner.

---

## 2. Agent Architecture

```mermaid
flowchart TD

    A[inquiry (Root Agent)]

    subgraph court_process (SequentialAgent)

        B[trial_loop (LoopAgent)]

        subgraph investigation (ParallelAgent)
            C[admirer - Defense]
            D[critic - Prosecution]
        end

        E[judge - requires exit_loop]

        F[verdict_writer]
        G[sentencing_agent]
        H[file_writer]

    end

    A --> B
    B --> C
    B --> D
    C --> E
    D --> E
    E -->|continue| B
    E -->|exit_loop| F
    F --> G
    G --> H
3. Agent Responsibilities
inquiry (Root Agent)
Receives topic from user

Stores topic in session state

Transfers control to court_process

court_process (SequentialAgent)
Enforces execution order:

trial_loop

verdict_writer

sentencing_agent

file_writer

Guarantees deterministic stage progression.

trial_loop (LoopAgent)
Runs investigation and judicial evaluation until evidence is sufficient.

Contains:

investigation (ParallelAgent)

judge (termination authority)

Loop termination is allowed only via exit_loop tool.

investigation (ParallelAgent)
Runs two agents simultaneously:

admirer (Defense)
Collects positive achievements

Writes to pos_data

critic (Prosecution)
Collects negative findings or controversies

Writes to neg_data

Parallel execution reduces bias and prevents sequential influence.

judge
Evaluates balance between pos_data and neg_data

Orders further research if insufficient

Writes neutral analysis to verdict

Must call exit_loop to end loop

verdict_writer
Generates structured legal opinion:

I. Background
II. Issues
III. Positive Findings
IV. Negative Findings
V. Legal Analysis
VI. Verdict

sentencing_agent
Applies international criminal law frameworks:

Rome Statute

Geneva Conventions

Crimes Against Humanity

Genocide

War Crimes

Crime of Aggression

Produces:

VII. International Legal Qualification
VIII. Hypothetical Sentencing Outcome

file_writer
Formats and saves the final A4-style report into:

historical_reports/<TOPIC>_Court_Report.txt
4. State Management
The system uses explicit session state keys:

Key	Purpose
topic	User input
pos_data	Positive findings
neg_data	Negative findings
verdict	Judge analysis
verdict_body	Sections I–VI
sentencing_body	Sections VII–VIII
Design principles:

Single-owner write access

Append-only for research data

Deterministic state propagation

No cross-agent mutation

5. Output Structure
Each execution produces a structured tribunal-style document:

THE HISTORICAL COURT
INTERNATIONAL TRIBUNAL DIVISION

I. BACKGROUND
II. ISSUES FOR DETERMINATION
III. FINDINGS OF FACT (POSITIVE)
IV. FINDINGS OF FACT (NEGATIVE)
V. LEGAL ANALYSIS
VI. VERDICT
VII. INTERNATIONAL LEGAL QUALIFICATION
VIII. HYPOTHETICAL SENTENCING OUTCOME
The output is:

Balanced

Legally structured

Deterministic

Based strictly on collected evidence

6. Technical Design Principles
Multi-Agent Orchestration
Root → Sequential → Loop → Parallel → Composition

Deterministic Loop Control
Loop terminates only via exit_loop

No natural-language termination allowed

Parallel Adversarial Modeling
Defense and Prosecution operate independently

Prevents bias

Tool Restriction (Anti-Hallucination)
Explicit tool whitelist

No delegation

temperature = 0 for reproducibility

Clean Responsibility Separation
Each agent has a single responsibility:

Research

Evaluation

Drafting

Legal qualification

File output

7. How to Run
Install dependencies:

pip install google-adk python-dotenv google-cloud-logging langchain-community wikipedia
Create .env:

MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your_api_key
Run CLI:

adk run TheHistoricalCourt
Or Web UI:

adk web TheHistoricalCourt
8. Grading Rubric Alignment
Agent Structure
✔ Root Agent
✔ SequentialAgent
✔ LoopAgent with exit_loop enforcement
✔ ParallelAgent
✔ Clear role separation

Output Completeness
✔ Positive findings
✔ Negative findings
✔ Judicial analysis
✔ International legal qualification
✔ Hypothetical sentencing
✔ Structured A4 legal format

Programming Technique
✔ OOP-based modular design
✔ Explicit state management
✔ Deterministic execution control
✔ Anti-hallucination safeguards
✔ Clean separation of concerns

9. Conclusion
The Historical Court demonstrates a structured, reproducible, and well-architected multi-agent system that simulates an international tribunal process with controlled logic, balanced evidence, and formal legal reporting.

Author:
The Historical Court Simulation Engine
