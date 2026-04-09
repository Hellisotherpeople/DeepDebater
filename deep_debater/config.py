"""Configuration for DeepDebater."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DebateConfig:
    """All configuration for a debate simulation.

    Only ``openai_api_key`` is required. Everything else has sensible defaults.
    """

    openai_api_key: str
    db_path: str = "debate_evidence_full_buzzhpc.duckdb"

    # LLM settings
    llm_model: str = "gpt-5.4-nano"
    temperature: float = 1.0
    top_p: float = 0.8

    # TTS settings
    enable_tts: bool = True
    voice_model: str = "gpt-4o-mini-tts"
    affirmative_voice: str = "alloy"
    negative_voice: str = "onyx"
    judge_voice: str = "fable"

    # Debate parameters
    num_advantages: int = 3
    plantext_search_iterations: int = 4
    evidence_search_max_iterations: int = 3
    on_case_rebuttals: int = 3
    cross_ex_questions: int = 4
    speech_draft_rounds: int = 2

    # Retry
    max_retries: int = 3

    # Output
    output_dir: str = "output"

    def _llm_entry(self, **extra) -> dict:
        """Build a config-list entry dict for AG2 ``LLMConfig``."""
        d = {"model": self.llm_model, "api_key": self.openai_api_key}
        d.update(extra)
        return d

    def base_llm(self):
        """Standard LLMConfig."""
        from autogen import LLMConfig
        return LLMConfig(
            self._llm_entry(),
            temperature=self.temperature,
            top_p=self.top_p,
            parallel_tool_calls=None,
        )

    def required_llm(self):
        """LLMConfig with tool_choice='required'."""
        from autogen import LLMConfig
        return LLMConfig(
            self._llm_entry(tool_choice="required"),
            temperature=self.temperature,
            top_p=self.top_p,
            parallel_tool_calls=None,
        )

    def structured_llm(self, response_format):
        """LLMConfig with structured output (Pydantic model)."""
        from autogen import LLMConfig
        return LLMConfig(
            self._llm_entry(),
            temperature=self.temperature,
            top_p=self.top_p,
            response_format=response_format,
            parallel_tool_calls=None,
        )
