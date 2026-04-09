"""CLI entry point for DeepDebater.

Usage:
    python -m deep_debater                          # Interactive TUI
    python -m deep_debater "Resolved: ..."          # TUI with preset topic
    python -m deep_debater --headless "Resolved: ..." # No TUI, just run
    python -m deep_debater --help
"""

from __future__ import annotations

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="deep_debater",
        description="DeepDebater - AI Policy Debate Simulator",
    )
    parser.add_argument(
        "topic",
        nargs="?",
        default=None,
        help="The debate resolution/topic",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (default: $OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--db",
        default="debate_evidence_full_buzzhpc.duckdb",
        help="Path to the DuckDB evidence database",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model to use (default: gpt-4.1-mini)",
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable text-to-speech audio generation",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without the TUI (prints to stdout)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "--advantages",
        type=int,
        default=3,
        help="Number of advantages to generate (default: 3)",
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY", "")
    if not api_key and not args.headless:
        # TUI will handle the error message
        pass
    elif not api_key:
        print("Error: OPENAI_API_KEY not set. Use --api-key or set the environment variable.")
        sys.exit(1)

    from deep_debater.config import DebateConfig

    config = DebateConfig(
        openai_api_key=api_key,
        db_path=args.db,
        llm_model=args.model,
        enable_tts=not args.no_tts,
        output_dir=args.output,
        num_advantages=args.advantages,
    )

    if args.headless:
        if not args.topic:
            print("Error: topic is required in headless mode")
            sys.exit(1)
        _run_headless(config, args.topic)
    else:
        from deep_debater.app import run_app
        run_app(config=config, topic=args.topic)


def _run_headless(config, topic):
    """Run a debate without the TUI."""
    from deep_debater.debate import Debate

    def on_event(evt):
        etype = evt.get("type", "")
        if etype == "step_start":
            print(f"\n{'='*60}")
            print(f"  {evt.get('step', '')}")
            print(f"{'='*60}")
        elif etype == "step_complete":
            print(f"  [done] {evt.get('step', '')}")
        elif etype == "step":
            print(f"  > {evt.get('message', '')}")
        elif etype == "evidence_found":
            print(f"  * Evidence found (iteration {evt.get('iteration', 0)})")

    debate = Debate(topic=topic, config=config)
    debate.on_event = on_event

    print(f"Debate Topic: {topic}")
    print(f"Model: {config.llm_model}")
    print(f"Database: {config.db_path}")
    print()

    state = debate.run()

    # Save transcript
    import os
    os.makedirs(config.output_dir, exist_ok=True)
    path = os.path.join(config.output_dir, "debate_transcript.html")
    with open(path, "w") as f:
        f.write(state.full_transcript)
    print(f"\nTranscript saved to {path}")


if __name__ == "__main__":
    main()
