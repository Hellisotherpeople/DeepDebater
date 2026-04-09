"""Rebuttal speeches: 1NR, 1AR, 2NR, 2AR."""

from __future__ import annotations

from typing import Callable

from deep_debater.agents import run_speech_draft
from deep_debater.config import DebateConfig
from deep_debater.prompts import speeches as sp


def _wrap(name: str, transcript: str) -> str:
    cls = name.lower().replace(" ", "-")
    return (
        f"\n<div class='{cls}-section'>"
        f"<h1>{name}</h1>"
        f"<div class='{cls}-transcript'>{transcript}</div>"
        f"</div>\n"
    )


def write_1nr(config, debate_case, neg_html, twoac_html, twonc_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC:\n{twoac_html}\n\n2NC:\n{twonc_html}\n\n"
        "Write a complete 1NR speech transcript. "
        "Be noticeably shorter than the 2NC and focus on distinct arguments."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.onenr_drafter(),
        coach_prompt=sp.onenr_coach(),
        context_message=ctx,
        on_event=on_event,
    )
    return _wrap("1NR Speech", transcript), transcript


def write_1ar(config, debate_case, neg_html, twoac_html, twonc_html, onenr_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC:\n{twoac_html}\n\n2NC:\n{twonc_html}\n\n"
        f"1NR:\n{onenr_html}\n\n"
        "Write a complete 1AR speech transcript."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.onear_drafter(),
        coach_prompt=sp.onear_coach(),
        context_message=ctx,
        on_event=on_event,
    )
    return _wrap("1AR Speech", transcript), transcript


def write_2nr(config, debate_case, neg_html, twoac_html, twonc_html, onenr_html, onear_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC:\n{twoac_html}\n\n2NC:\n{twonc_html}\n\n"
        f"1NR:\n{onenr_html}\n\n1AR:\n{onear_html}\n\n"
        "Write a complete 2NR speech transcript."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.twonr_drafter(),
        coach_prompt=sp.twonr_coach(),
        context_message=ctx,
        on_event=on_event,
    )
    return _wrap("2NR Speech", transcript), transcript


def write_2ar(config, debate_case, neg_html, twoac_html, twonc_html, onenr_html, onear_html, twonr_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC:\n{twoac_html}\n\n2NC:\n{twonc_html}\n\n"
        f"1NR:\n{onenr_html}\n\n1AR:\n{onear_html}\n\n"
        f"2NR:\n{twonr_html}\n\n"
        "Write a complete 2AR speech transcript."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.twoar_drafter(),
        coach_prompt=sp.twoar_coach(),
        context_message=ctx,
        on_event=on_event,
    )
    return _wrap("2AR Speech", transcript), transcript


def judge_decision(config, debate_case, neg_html, twoac_html, twonc_html, onenr_html, onear_html, twonr_html, twoar_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC:\n{twoac_html}\n\n2NC:\n{twonc_html}\n\n"
        f"1NR:\n{onenr_html}\n\n1AR:\n{onear_html}\n\n"
        f"2NR:\n{twonr_html}\n\n2AR:\n{twoar_html}\n\n"
        "You are the judge. Decide who won and write a detailed RFD."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.judge_drafter(),
        coach_prompt=sp.judge_coach(),
        context_message=ctx,
        max_rounds=2,
        on_event=on_event,
    )
    return _wrap("Judge Decision and RFD", transcript), transcript
