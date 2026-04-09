"""Textual TUI application for DeepDebater."""

from __future__ import annotations

from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
    Label,
    RichLog,
    Static,
)

from deep_debater.config import DebateConfig
from deep_debater.debate import DEBATE_STEPS, Debate


# ---------------------------------------------------------------------------
# Step display widget
# ---------------------------------------------------------------------------

class StepIndicator(Static):
    """Shows a single debate step with status icon."""

    STEP_ICONS = {"pending": "  ", "active": ">>> ", "done": "  ", "error": "  "}

    status = reactive("pending")
    step_name = reactive("")

    def __init__(self, step_name: str, **kwargs):
        super().__init__(**kwargs)
        self.step_name = step_name

    def render(self) -> str:
        icon = self.STEP_ICONS.get(self.status, "  ")
        return f"{icon}{self.step_name}"

    def watch_status(self, new_status: str):
        self.remove_class("pending", "active", "done", "error")
        self.add_class(new_status)


class DebateFlow(VerticalScroll):
    """Left panel: shows all debate steps with progress indicators."""

    DEFAULT_CSS = """
    DebateFlow {
        width: 30;
        border: solid $primary;
        padding: 1;
    }
    DebateFlow StepIndicator {
        height: 1;
        color: $text-muted;
    }
    DebateFlow StepIndicator.active {
        color: $warning;
        text-style: bold;
    }
    DebateFlow StepIndicator.done {
        color: $success;
    }
    DebateFlow StepIndicator.error {
        color: $error;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indicators: dict[str, StepIndicator] = {}

    def compose(self) -> ComposeResult:
        yield Label("[bold]Debate Flow[/bold]")
        yield Label("")
        for step in DEBATE_STEPS:
            indicator = StepIndicator(step)
            self.indicators[step] = indicator
            yield indicator

    def set_active(self, step: str):
        for name, ind in self.indicators.items():
            if name == step:
                ind.status = "active"
            elif ind.status == "active":
                ind.status = "pending"

    def set_done(self, step: str):
        if step in self.indicators:
            self.indicators[step].status = "done"

    def set_error(self, step: str):
        if step in self.indicators:
            self.indicators[step].status = "error"


# ---------------------------------------------------------------------------
# Status bar
# ---------------------------------------------------------------------------

class StatusBar(Static):
    """Shows current activity and sub-step progress."""

    DEFAULT_CSS = """
    StatusBar {
        height: 3;
        border: solid $accent;
        padding: 0 1;
    }
    """

    message = reactive("Ready to debate!")

    def render(self) -> str:
        return f"[bold]{self.message}[/bold]"


# ---------------------------------------------------------------------------
# Main output panel
# ---------------------------------------------------------------------------

class OutputPanel(RichLog):
    """Right panel: shows live output of the debate."""

    DEFAULT_CSS = """
    OutputPanel {
        border: solid $secondary;
    }
    """


# ---------------------------------------------------------------------------
# Topic input screen
# ---------------------------------------------------------------------------

class TopicInput(Static):
    """Initial screen for entering the debate topic."""

    DEFAULT_CSS = """
    TopicInput {
        align: center middle;
        width: 80;
        height: 12;
        border: double $primary;
        padding: 2;
    }
    """

    def compose(self) -> ComposeResult:
        from textual.widgets import Input, Button

        yield Label("[bold]DeepDebater[/bold] - AI Policy Debate Simulator\n")
        yield Label("Enter the debate resolution:")
        yield Input(
            placeholder="Resolved: The United States should...",
            id="topic-input",
        )
        yield Label("")
        yield Button("Start Debate", variant="primary", id="start-btn")


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class DeepDebaterApp(App):
    """The DeepDebater TUI application."""

    TITLE = "DeepDebater"
    SUB_TITLE = "AI Policy Debate Simulator"

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
    }

    #debate-screen {
        layout: horizontal;
        display: none;
    }

    #topic-screen {
        align: center middle;
        height: 100%;
    }

    .visible {
        display: block !important;
    }

    DebateFlow {
        width: 32;
        min-width: 28;
    }

    #right-panel {
        width: 1fr;
    }
    """

    BINDINGS: ClassVar = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, config: DebateConfig | None = None, topic: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._config = config
        self._topic = topic
        self._debate: Debate | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        if self._topic:
            # Skip topic input, go straight to debate
            yield self._make_debate_screen()
        else:
            yield Vertical(TopicInput(), id="topic-screen")
            yield self._make_debate_screen()
        yield Footer()

    def _make_debate_screen(self) -> Horizontal:
        return Horizontal(
            DebateFlow(),
            Vertical(
                StatusBar(),
                OutputPanel(highlight=True, markup=True),
                id="right-panel",
            ),
            id="debate-screen",
        )

    def on_mount(self):
        if self._topic:
            screen = self.query_one("#debate-screen")
            screen.add_class("visible")
            self._start_debate(self._topic)

    def on_button_pressed(self, event) -> None:
        if event.button.id != "start-btn":
            return
        from textual.widgets import Input
        topic_input = self.query_one("#topic-input", Input)
        topic = topic_input.value.strip()
        if not topic:
            return

        # Hide topic screen, show debate screen
        self.query_one("#topic-screen").styles.display = "none"
        screen = self.query_one("#debate-screen")
        screen.add_class("visible")
        self._start_debate(topic)

    def _start_debate(self, topic: str):
        if not self._config:
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                self.query_one(OutputPanel).write(
                    "[red]Error: OPENAI_API_KEY not set. "
                    "Set it as an environment variable or pass a DebateConfig.[/red]"
                )
                return
            self._config = DebateConfig(openai_api_key=api_key)

        self._debate = Debate(topic=topic, config=self._config)
        self._debate.on_event = self._handle_debate_event

        output = self.query_one(OutputPanel)
        output.write(f"[bold green]Debate Topic:[/bold green] {topic}\n")
        output.write("[dim]Starting debate...[/dim]\n")

        self._run_debate()

    @work(thread=True)
    def _run_debate(self):
        try:
            self._debate.run()
            self.call_from_thread(self._on_debate_complete)
        except Exception as e:
            self.call_from_thread(self._on_debate_error, str(e))

    def _handle_debate_event(self, event: dict):
        """Called from the debate thread when events occur."""
        evt_type = event.get("type", "")

        if evt_type == "step_start":
            step = event.get("step", "")
            self.call_from_thread(self._update_step_start, step)

        elif evt_type == "step_complete":
            step = event.get("step", "")
            self.call_from_thread(self._update_step_complete, step)

        elif evt_type == "step":
            msg = event.get("message", "")
            self.call_from_thread(self._update_status, msg)

        elif evt_type == "evidence_found":
            iteration = event.get("iteration", 0)
            self.call_from_thread(
                self._log, f"[green]Evidence found (iteration {iteration})[/green]"
            )

        elif evt_type == "iteration":
            count = event.get("count", 0)
            self.call_from_thread(
                self._log, f"[dim]Search iteration {count}...[/dim]"
            )

    def _update_step_start(self, step: str):
        flow = self.query_one(DebateFlow)
        flow.set_active(step)
        status = self.query_one(StatusBar)
        status.message = f"Working on: {step}"
        output = self.query_one(OutputPanel)
        output.write(f"\n[bold yellow]{'='*50}[/bold yellow]")
        output.write(f"[bold yellow]  {step}[/bold yellow]")
        output.write(f"[bold yellow]{'='*50}[/bold yellow]\n")

    def _update_step_complete(self, step: str):
        flow = self.query_one(DebateFlow)
        flow.set_done(step)
        output = self.query_one(OutputPanel)
        output.write(f"[green]  {step} complete![/green]\n")

    def _update_status(self, msg: str):
        status = self.query_one(StatusBar)
        status.message = msg
        output = self.query_one(OutputPanel)
        output.write(f"  [dim]{msg}[/dim]")

    def _log(self, msg: str):
        self.query_one(OutputPanel).write(f"  {msg}")

    def _on_debate_complete(self):
        status = self.query_one(StatusBar)
        status.message = "Debate complete!"
        output = self.query_one(OutputPanel)
        output.write("\n[bold green]" + "=" * 50 + "[/bold green]")
        output.write("[bold green]  DEBATE COMPLETE![/bold green]")
        output.write("[bold green]" + "=" * 50 + "[/bold green]")

        # Save transcript
        if self._debate:
            import os
            os.makedirs(self._config.output_dir, exist_ok=True)
            path = os.path.join(self._config.output_dir, "debate_transcript.html")
            with open(path, "w") as f:
                f.write(self._debate.state.full_transcript)
            output.write(f"\n[dim]Transcript saved to {path}[/dim]")

    def _on_debate_error(self, error: str):
        status = self.query_one(StatusBar)
        status.message = "Error!"
        output = self.query_one(OutputPanel)
        output.write(f"\n[red bold]Error: {error}[/red bold]")


def run_app(config: DebateConfig | None = None, topic: str | None = None):
    """Launch the DeepDebater TUI."""
    app = DeepDebaterApp(config=config, topic=topic)
    app.run()
