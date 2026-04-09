"""High-level Debate orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from deep_debater.config import DebateConfig
from deep_debater.tts import generate_speech, strip_html
from deep_debater.workflows import constructives, cross_ex, evidence, negative, rebuttals


@dataclass
class DebateState:
    """Accumulated state of a debate round."""

    topic: str = ""
    plantext: str = ""

    # Speech HTML strings (built incrementally)
    debate_case: str = ""       # 1AC
    neg_html: str = ""          # 1NC
    twoac_html: str = ""        # 2AC
    twonc_html: str = ""        # 2NC
    onenr_html: str = ""        # 1NR
    onear_html: str = ""        # 1AR
    twonr_html: str = ""        # 2NR
    twoar_html: str = ""        # 2AR
    judge_html: str = ""        # Judge decision

    # Cross-examination transcripts
    cx_1ac_html: str = ""
    cx_1nc_html: str = ""
    cx_2ac_html: str = ""
    cx_2nc_html: str = ""

    # Metadata
    negative_positions: dict = field(default_factory=dict)
    current_step: str = ""
    completed_steps: list[str] = field(default_factory=list)

    @property
    def full_transcript(self) -> str:
        """Return the complete debate transcript as HTML."""
        parts = [
            self.debate_case,
            self.cx_1ac_html,
            self.neg_html,
            self.cx_1nc_html,
            self.twoac_html,
            self.cx_2ac_html,
            self.twonc_html,
            self.cx_2nc_html,
            self.onenr_html,
            self.onear_html,
            self.twonr_html,
            self.twoar_html,
            self.judge_html,
        ]
        return "\n".join(p for p in parts if p)


# The ordered sequence of debate steps
DEBATE_STEPS = [
    "1AC",
    "CX of 1AC",
    "1NC",
    "CX of 1NC",
    "2AC",
    "CX of 2AC",
    "2NC",
    "CX of 2NC",
    "1NR",
    "1AR",
    "2NR",
    "2AR",
    "Judge Decision",
]


class Debate:
    """Orchestrates a full policy debate round.

    Basic usage::

        from deep_debater import Debate, DebateConfig

        config = DebateConfig(openai_api_key="sk-...")
        debate = Debate(
            topic="Resolved: The US should establish a Department of Fun",
            config=config,
        )
        debate.run()
        print(debate.state.full_transcript)

    For TUI integration, register an event callback::

        debate.on_event = lambda evt: print(evt)
        debate.run()
    """

    def __init__(self, topic: str, config: DebateConfig):
        self.config = config
        self.state = DebateState(topic=topic)
        self.on_event: Callable | None = None

    def _emit(self, event_type: str, **kwargs):
        if self.on_event:
            self.on_event({"type": event_type, **kwargs})

    def _retry(self, fn, *args, **kwargs):
        last_exc = None
        for _ in range(self.config.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
        raise last_exc

    def _tts(self, text: str, filename: str, voice: str):
        """Generate TTS if enabled."""
        if self.config.enable_tts:
            import os
            path = os.path.join(self.config.output_dir, filename)
            generate_speech(self.config, strip_html(text), path, voice)

    # ------------------------------------------------------------------
    # Individual step methods (can be called independently)
    # ------------------------------------------------------------------

    def build_1ac(self):
        """Build the 1AC (First Affirmative Constructive)."""
        self._emit("step_start", step="1AC")
        self.state.debate_case = evidence.build_1ac(
            self.config, self.state.topic, on_event=self.on_event
        )
        self.state.completed_steps.append("1AC")
        self._emit("step_complete", step="1AC")

    def cx_of_1ac(self):
        """Cross-examination of the 1AC."""
        self._emit("step_start", step="CX of 1AC")
        html, pairs = self._retry(
            cross_ex.cross_examine_1ac,
            self.config, self.state.debate_case, self.on_event,
        )
        self.state.cx_1ac_html = html
        self.state.debate_case += html
        self.state.completed_steps.append("CX of 1AC")
        self._emit("step_complete", step="CX of 1AC")

    def build_1nc(self):
        """Build the 1NC (First Negative Constructive)."""
        self._emit("step_start", step="1NC")
        self.state.neg_html, self.state.negative_positions = negative.build_1nc(
            self.config, self.state.debate_case, on_event=self.on_event
        )
        self.state.completed_steps.append("1NC")
        self._emit("step_complete", step="1NC")

    def cx_of_1nc(self):
        """Cross-examination of the 1NC."""
        self._emit("step_start", step="CX of 1NC")
        html, pairs = self._retry(
            cross_ex.cross_examine_1nc,
            self.config, self.state.debate_case, self.state.neg_html, self.on_event,
        )
        self.state.cx_1nc_html = html
        self.state.neg_html += html
        self.state.completed_steps.append("CX of 1NC")
        self._emit("step_complete", step="CX of 1NC")

    def build_2ac(self):
        """Build the 2AC (Second Affirmative Constructive)."""
        self._emit("step_start", step="2AC")
        twoac_html, cards = self._retry(
            constructives.gather_2ac_evidence,
            self.config, self.state.debate_case, self.state.neg_html, self.on_event,
        )
        twoac_html, transcript = self._retry(
            constructives.write_2ac_speech,
            self.config, self.state.debate_case, self.state.neg_html, twoac_html, self.on_event,
        )
        self.state.twoac_html = twoac_html
        self.state.completed_steps.append("2AC")
        self._emit("step_complete", step="2AC")

    def cx_of_2ac(self):
        """Cross-examination of the 2AC."""
        self._emit("step_start", step="CX of 2AC")
        html, pairs = self._retry(
            cross_ex.cross_examine_2ac,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.on_event,
        )
        self.state.cx_2ac_html = html
        self.state.twoac_html += html
        self.state.completed_steps.append("CX of 2AC")
        self._emit("step_complete", step="CX of 2AC")

    def build_2nc(self):
        """Build the 2NC (Second Negative Constructive)."""
        self._emit("step_start", step="2NC")
        twonc_html, cards = self._retry(
            constructives.gather_2nc_evidence,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.on_event,
        )
        twonc_html, transcript = self._retry(
            constructives.write_2nc_speech,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, twonc_html, self.on_event,
        )
        self.state.twonc_html = twonc_html
        self.state.completed_steps.append("2NC")
        self._emit("step_complete", step="2NC")

    def cx_of_2nc(self):
        """Cross-examination of the 2NC."""
        self._emit("step_start", step="CX of 2NC")
        html, pairs = self._retry(
            cross_ex.cross_examine_2nc,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.state.twonc_html, self.on_event,
        )
        self.state.cx_2nc_html = html
        self.state.twonc_html += html
        self.state.completed_steps.append("CX of 2NC")
        self._emit("step_complete", step="CX of 2NC")

    def build_1nr(self):
        """Build the 1NR (First Negative Rebuttal)."""
        self._emit("step_start", step="1NR")
        self.state.onenr_html, _ = self._retry(
            rebuttals.write_1nr,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.state.twonc_html, self.on_event,
        )
        self.state.completed_steps.append("1NR")
        self._emit("step_complete", step="1NR")

    def build_1ar(self):
        """Build the 1AR (First Affirmative Rebuttal)."""
        self._emit("step_start", step="1AR")
        self.state.onear_html, _ = self._retry(
            rebuttals.write_1ar,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.state.twonc_html,
            self.state.onenr_html, self.on_event,
        )
        self.state.completed_steps.append("1AR")
        self._emit("step_complete", step="1AR")

    def build_2nr(self):
        """Build the 2NR (Second Negative Rebuttal)."""
        self._emit("step_start", step="2NR")
        self.state.twonr_html, _ = self._retry(
            rebuttals.write_2nr,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.state.twonc_html,
            self.state.onenr_html, self.state.onear_html, self.on_event,
        )
        self.state.completed_steps.append("2NR")
        self._emit("step_complete", step="2NR")

    def build_2ar(self):
        """Build the 2AR (Second Affirmative Rebuttal)."""
        self._emit("step_start", step="2AR")
        self.state.twoar_html, _ = self._retry(
            rebuttals.write_2ar,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.state.twonc_html,
            self.state.onenr_html, self.state.onear_html,
            self.state.twonr_html, self.on_event,
        )
        self.state.completed_steps.append("2AR")
        self._emit("step_complete", step="2AR")

    def judge(self):
        """Judge decision and RFD."""
        self._emit("step_start", step="Judge Decision")
        self.state.judge_html, _ = self._retry(
            rebuttals.judge_decision,
            self.config, self.state.debate_case, self.state.neg_html,
            self.state.twoac_html, self.state.twonc_html,
            self.state.onenr_html, self.state.onear_html,
            self.state.twonr_html, self.state.twoar_html, self.on_event,
        )
        self.state.completed_steps.append("Judge Decision")
        self._emit("step_complete", step="Judge Decision")

    # ------------------------------------------------------------------
    # Run the full debate
    # ------------------------------------------------------------------

    def run(self):
        """Run the complete debate round from 1AC through judge decision."""
        self.build_1ac()
        self.cx_of_1ac()
        self.build_1nc()
        self.cx_of_1nc()
        self.build_2ac()
        self.cx_of_2ac()
        self.build_2nc()
        self.cx_of_2nc()
        self.build_1nr()
        self.build_1ar()
        self.build_2nr()
        self.build_2ar()
        self.judge()
        return self.state
