# FactCheck AI — Multi-Source Autonomous Fact Checker

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1%2B-purple)
![OpenAI GPT-4o](https://img.shields.io/badge/OpenAI-GPT--4o-green)
![Tavily Search](https://img.shields.io/badge/Tavily-Search-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)

FactCheck AI is an autonomous multi-source fact-checking agent that verifies any claim by deconstructing it into atomic sub-claims, searching the web for evidence, evaluating each sub-claim with a confidence score, detecting logical fallacies, and producing a comprehensive structured report — all in a single pipeline run.

What makes FactCheck AI unique is its **conditional routing loop**: after initial evidence gathering and evaluation, the LangGraph state machine checks whether any sub-claim has a confidence score below 60%. If so, the agent automatically generates more targeted search queries and performs a second pass of deep research before proceeding — up to 2 extra iterations. This ensures low-confidence claims receive additional scrutiny without spiralling into infinite loops.

---

## Architecture

```
Claim Input
    │
    ▼
┌─────────────────┐
│  Deconstructor  │ — Breaks claim into atomic sub-claims
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Researcher    │ — Searches for + and - evidence per sub-claim
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Evaluator    │ — Verdicts + confidence per sub-claim
└────────┬────────┘
         │
    ┌────▼────────────────────────────┐
    │  Confidence < 60% detected?     │
    └────┬──────────────┬─────────────┘
         │ YES          │ NO (or max iterations reached)
         ▼              ▼
┌──────────────┐   ┌──────────────────┐
│Deep Researcher│   │ Fallacy Detector │
│(targeted re- │   └────────┬─────────┘
│ search)      │            │
└──────┬───────┘            ▼
       │              ┌──────────┐
       └──────────────▶ Writer   │
       (loops back    └────┬─────┘
        to Evaluator)      │
                           ▼
                    Final Report + UI
```

---

## Verdict Definitions

| Verdict | Meaning |
|---|---|
| ✅ TRUE | Supported by credible evidence |
| ❌ FALSE | Contradicted by credible evidence |
| ⚠️ MISLEADING | True but missing crucial context |
| ❓ UNVERIFIABLE | Insufficient evidence to determine |
| ⚖️ DISPUTED | Credible sources actively disagree |

---

## Prerequisites

- Python 3.11 or higher
- An [OpenAI API key](https://platform.openai.com/api-keys) (GPT-4o access required)
- A [Tavily API key](https://tavily.com/) (free tier available)

---

## Installation

1. Clone the repository or create the project directory:
   ```bash
   git clone <repo-url> fact_checker
   # or just cd into the existing directory
   ```

2. Navigate to the project directory:
   ```bash
   cd fact_checker
   ```

3. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   ```

6. Launch the application:
   ```bash
   python -m streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`.

---

## Usage

1. Paste any claim, headline, or statement into the text box
2. Click **🔍 Fact Check**
3. Watch the agent work in real time through the status panel
4. Review the colour-coded verdict, sub-claim breakdown, and full report
5. Download the report as `.md` or `.txt`

Use the **⚡ Example claims** in the sidebar to try pre-loaded examples instantly.

---

## Cost Estimates

Each fact-check costs approximately **$0.01–$0.05** with GPT-4o depending on:
- Number of sub-claims generated (3–6 typically)
- Whether deep research iterations are triggered
- Length of the final report

Complex claims with multiple deep research passes may cost up to $0.10.

---

## Extending the Project

1. **Source credibility scoring** — integrate domain authority APIs or a known-bias database (e.g., AllSides, Media Bias/Fact Check) to weight source quality in confidence calculations
2. **Styled PDF export** — use `reportlab` or `weasyprint` to generate a branded PDF fact-check certificate users can share
3. **Historical claims database** — add a SQLite cache that stores past fact-checks by claim hash, enabling instant results for previously checked claims and trend analysis
4. **Browser extension** — build a Chrome/Firefox extension that highlights claims on any web page and sends them to a deployed FactCheck AI API endpoint for inline verification

---
