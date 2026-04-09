# DeepDebater

A Python TUI library for fully automated, AI-driven competitive policy debate simulation.

DeepDebater uses multi-agent orchestration (via [AG2](https://docs.ag2.ai/)) to simulate a complete policy debate round: both teams research evidence from a DuckDB database, construct cases, cross-examine each other, deliver rebuttals, and a judge renders a decision with a detailed RFD.

## Quick Start

```bash
pip install -e ".[tts]"

# Interactive TUI
python -m deep_debater

# With a preset topic
python -m deep_debater "Resolved: The United States should establish a Department of Fun"

# Headless mode (no TUI)
python -m deep_debater --headless "Resolved: The US should go to Mars"
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="sk-..."
```

## Python API

### Simple (3 lines)

```python
from deep_debater import Debate, DebateConfig

debate = Debate(
    topic="Resolved: The US should establish a Department of Fun",
    config=DebateConfig(openai_api_key="sk-..."),
)
state = debate.run()
print(state.full_transcript)
```

### Run individual steps

```python
debate = Debate(topic="...", config=config)
debate.build_1ac()
debate.cx_of_1ac()
debate.build_1nc()
# ... or debate.run() for the full round
```

### Customize everything

```python
config = DebateConfig(
    openai_api_key="sk-...",
    llm_model="gpt-5.4-nano",       # Default; also works with gpt-4.1-mini, etc.
    db_path="my_evidence.duckdb",    # BM25 evidence database
    num_advantages=2,                # Default 3
    evidence_search_max_iterations=5,
    cross_ex_questions=7,
    enable_tts=False,                # Disable audio generation
    affirmative_voice="nova",        # OpenAI TTS voices
    negative_voice="echo",
    temperature=1.5,
)
```

### Event callbacks (for custom UIs)

```python
def on_event(evt):
    if evt["type"] == "step_start":
        print(f"Starting: {evt['step']}")
    elif evt["type"] == "evidence_found":
        print(f"Found evidence (iteration {evt['iteration']})")

debate.on_event = on_event
debate.run()
```

## Debate Flow

A complete round follows standard policy debate structure:

| Step | Description |
|------|-------------|
| **1AC** | Affirmative constructive: plantext, harms, inherency, advantages (uniqueness/link/internal link/impact), solvency |
| **CX of 1AC** | Negative cross-examines the 1AC |
| **1NC** | Negative constructive: topicality, theory, disadvantage, counterplan, kritik, on-case rebuttals |
| **CX of 1NC** | Affirmative cross-examines the 1NC |
| **2AC** | Second affirmative constructive with new evidence and speech |
| **CX of 2AC** | Negative cross-examines the 2AC |
| **2NC** | Second negative constructive with new evidence and speech |
| **CX of 2NC** | Affirmative cross-examines the 2NC |
| **1NR** | First negative rebuttal |
| **1AR** | First affirmative rebuttal |
| **2NR** | Second negative rebuttal |
| **2AR** | Second affirmative rebuttal |
| **Judge** | Judge decision with detailed Reason for Decision (RFD) |

## Architecture

```
deep_debater/
├── __init__.py          # Public API: Debate, DebateConfig
├── __main__.py          # CLI entry point
├── config.py            # DebateConfig dataclass
├── db.py                # DuckDB + BM25 search
├── models.py            # Pydantic models for structured LLM output
├── agents.py            # 4 reusable agent workflow factories
├── tts.py               # Text-to-speech (optional)
├── prompts/             # System prompts for all agent roles
│   ├── affirmative.py
│   ├── negative.py
│   └── speeches.py
├── workflows/           # Thin wrappers composing agents + prompts
│   ├── evidence.py      # 1AC construction
│   ├── negative.py      # 1NC construction
│   ├── constructives.py # 2AC/2NC
│   ├── rebuttals.py     # 1NR/1AR/2NR/2AR + judge
│   └── cross_ex.py      # All 4 cross-examination periods
├── debate.py            # High-level Debate orchestrator
└── app.py               # Textual TUI
```

The key design insight: the original notebook had ~25 nearly-identical 150-line functions for evidence search. `agents.py` collapses these into 4 reusable factories:

- **`run_evidence_search()`** -- 4-agent group chat for finding and evaluating evidence
- **`run_iterative_generation()`** -- search-and-refine loop for generating positions
- **`run_speech_draft()`** -- drafter + coach speech writing
- **`run_cross_examination()`** -- alternating Q&A with structured summary

Each workflow function is now 5-15 lines instead of 150+.

## Requirements

- Python >= 3.10
- [AG2](https://pypi.org/project/ag2/) >= 0.6, < 1.0 (with OpenAI support)
- DuckDB evidence database (see original notebook for database setup)
- OpenAI API key

## CLI Options

```
python -m deep_debater [OPTIONS] [TOPIC]

Options:
  --api-key TEXT       OpenAI API key (default: $OPENAI_API_KEY)
  --db TEXT            Path to DuckDB evidence database
  --model TEXT         OpenAI model (default: gpt-5.4-nano)
  --no-tts             Disable text-to-speech
  --headless           Run without the TUI
  --output TEXT        Output directory (default: output)
  --advantages INT     Number of advantages (default: 3)
```

## Original Notebook

The original Jupyter notebook (`debate_case_creation_to_distribute.ipynb`) is preserved in this repo. See `README_ORIGINAL.md` for the original project documentation.

## License

MIT
