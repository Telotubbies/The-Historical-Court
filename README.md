# THE HISTORICAL COURT  
### Multi-Agent International Tribunal Simulation using Google ADK

---

## 📌 Project Overview

**The Historical Court** is a Multi-Agent System built using **Google ADK** that simulates a structured international tribunal.

The system evaluates historical figures or events using:

- Parallel investigation (Prosecution vs Defense)
- Judicial review loop
- International Criminal Law qualification
- Hypothetical sentencing phase
- Structured A4-style legal report output

This project follows a strict architectural pattern required by the assignment rubric:
- Sequential Agent
- Parallel Agent
- Loop Agent (must use `exit_loop`)
- State separation
- Wikipedia research refinement
- Formal legal output formatting

---

# 🏛 System Architecture

## 🔁 Multi-Agent Flow (Mermaid Diagram)

```mermaid
flowchart TD

    A[Root Agent: Inquiry] --> B[SequentialAgent: court_process]

    B --> C[LoopAgent: trial_loop]

    C --> D[ParallelAgent: investigation]

    D --> E[Admirer Agent<br>Defense]
    D --> F[Critic Agent<br>Prosecution]

    C --> G[Judge Agent<br>exit_loop required]

    B --> H[Verdict Writer Agent]
    H --> I[Sentencing Agent]

    I --> J[File Writer Agent]
