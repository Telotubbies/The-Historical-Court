
![สถาปัตยกรรม The Historical Court](image/README/1771512342119.png)

---# THE HISTORICAL COURT
## Deterministic Multi-Agent International Tribunal Simulation (Google ADK)

---

## 1. Overview

**The Historical Court** is a deterministic multi-agent system built using Google ADK.

It simulates an international tribunal workflow that:

- Conducts adversarial parallel investigation
- Applies judicial supervisory logic
- Enforces deterministic loop termination
- Performs structured legal drafting
- Applies international criminal law frameworks
- Generates an A4-style tribunal report

This is not a prompt chain.
It is a staged, layered orchestration architecture.

Primary data source: Wikipedia  
All models use `temperature=0` for reproducibility.

---

## 2. System Architecture

### 2.1 Layered Agent Architecture

```mermaid
flowchart TD

    subgraph L1["Layer 1 — Entry"]
        A[inquiry<br/>Root Agent]
    end

    subgraph L2["Layer 2 — Orchestration"]
        B[court_process<br/>SequentialAgent]
    end

    subgraph L3["Layer 3 — Supervisory Loop"]
        C[trial_loop<br/>LoopAgent]
    end

    subgraph L4["Layer 4 — Parallel Investigation"]
        D[admirer<br/>Defense]
        E[critic<br/>Prosecution]
    end

    subgraph L5["Layer 5 — Judicial Gate"]
        F[judge<br/>exit_loop required]
    end

    subgraph L6["Layer 6 — Composition"]
        G[verdict_writer]
        H[sentencing_agent]
        I[file_writer]
    end

    A --> B
    B --> C
    C --> D
    C --> E
    D --> F
    E --> F
    F -->|continue| C
    F -->|exit_loop| G
    G --> H --> I
2.2 Control Flow Semantics
Execution order:

inquiry
→ trial_loop
    → investigation (parallel)
    → judge
→ verdict_writer
→ sentencing_agent
→ file_writer
Why SequentialAgent?

Verdict must not run before judicial validation

Sentencing depends on verdict

File writing depends on both

Deterministic stage boundaries

2.3 Supervisory Loop Model
flowchart TD
    A[investigation] --> B[judge]
    B -->|insufficient evidence| A
    B -->|exit_loop| C[next stage]
Loop guarantees:

Minimum evidence threshold

Evidence balance enforcement

Deterministic termination via exit_loop

No natural language termination

2.4 Parallel Adversarial Model
ParallelAgent runs:

admirer (Defense)

critic (Prosecution)

Benefits:

Independent research

Reduced bias

Symmetric adversarial modeling

No sequential influence

3. State Architecture
3.1 State Flow
flowchart LR

    inquiry -->|set_state| topic

    admirer -->|append| pos_data
    critic -->|append| neg_data

    judge -->|append| verdict

    verdict_writer -->|output_key| verdict_body
    sentencing_agent -->|output_key| sentencing_body

    file_writer --> verdict_body
    file_writer --> sentencing_body
3.2 State Contract
Key	Owner	Type	Write Mode
topic	inquiry	string	set
pos_data	admirer	list	append
neg_data	critic	list	append
verdict	judge	list	append
verdict_body	verdict_writer	string	overwrite
sentencing_body	sentencing_agent	string	overwrite
Design Principles:

Single-writer ownership

Append-only research data

Deterministic propagation

No cross-agent mutation

4. Message-Level Sequence
sequenceDiagram
    participant User
    participant Inquiry
    participant Investigation
    participant Judge
    participant Verdict
    participant Sentencing
    participant FileWriter

    User->>Inquiry: Provide topic
    Inquiry->>Investigation: Start loop
    Investigation->>Judge: Submit evidence
    Judge-->>Investigation: Continue (if needed)
    Judge->>Verdict: exit_loop
    Verdict->>Sentencing: Provide analysis
    Sentencing->>FileWriter: Provide legal sections
    FileWriter->>User: Report generated
5. Legal Reasoning Layer
Sentencing agent evaluates under:

Rome Statute (ICC)

Geneva Conventions

Crimes Against Humanity

Genocide

War Crimes

Crime of Aggression

Retroactivity

Jurisdiction

Produces:

VII. International Legal Qualification
VIII. Hypothetical Sentencing Outcome
Separation ensures:

Research logic ≠ Legal classification logic

Clean legal reasoning layer

6. Anti-Hallucination Controls
Control	Purpose
Tool whitelist	Prevent hallucinated tool calls
Explicit tool restriction	Prevent delegation
exit_loop enforcement	Deterministic termination
temperature=0	Reproducible outputs
Strict state keys	Prevent mutation
7. Component Dependency Graph
flowchart LR
    inquiry --> court_process
    court_process --> trial_loop
    trial_loop --> investigation
    trial_loop --> judge
    investigation --> admirer
    investigation --> critic
    judge --> verdict_writer
    verdict_writer --> sentencing_agent
    sentencing_agent --> file_writer
