"""Cross-examination workflows for all four CX periods."""

from __future__ import annotations

from deep_debater.agents import run_cross_examination
from deep_debater.config import DebateConfig
from deep_debater.models import CrossExAffAsks, CrossExNegAsks
from deep_debater.prompts import speeches as sp


def _format_neg_asks(pairs: list[dict]) -> str:
    html = ""
    for i, p in enumerate(pairs, 1):
        html += f"<div><b>Negative Q{i}:</b> {p['negative_question']}</div>\n"
        html += f"<div><b>Affirmative A{i}:</b> {p['affirmative_response']}</div><br/>\n"
    return html


def _format_aff_asks(pairs: list[dict]) -> str:
    html = ""
    for i, p in enumerate(pairs, 1):
        html += f"<div><b>Affirmative Q{i}:</b> {p['affirmative_question']}</div>\n"
        html += f"<div><b>Negative A{i}:</b> {p['negative_response']}</div><br/>\n"
    return html


def cross_examine_1ac(config: DebateConfig, debate_case: str, on_event=None):
    """1NC cross-examines the 1AC. Returns (html, pairs)."""
    pairs = run_cross_examination(
        config=config,
        questioner_prompt=sp.cx_neg_questions_1ac(),
        responder_prompt=sp.cx_aff_answers_1ac(),
        summary_prompt=sp.cx_summary("1NC cross-examination of the 1AC"),
        response_model=CrossExNegAsks,
        context_message=(
            f"The 1AC is:\n\n{debate_case}\n\nBegin by asking your first question."
        ),
        num_questions=config.cross_ex_questions,
        on_event=on_event,
    )
    html = f"<h2>1NC Cross-Examination of the 1AC</h2>\n{_format_neg_asks(pairs)}"
    return html, pairs


def cross_examine_1nc(config, debate_case, neg_html, on_event=None):
    """1AC cross-examines the 1NC. Returns (html, pairs)."""
    pairs = run_cross_examination(
        config=config,
        questioner_prompt=sp.cx_aff_questions_1nc(),
        responder_prompt=sp.cx_neg_answers_1nc(),
        summary_prompt=sp.cx_summary("1AC cross-examination of the 1NC"),
        response_model=CrossExAffAsks,
        context_message=(
            f"The 1AC is:\n\n{debate_case}\n\n"
            f"The 1NC is:\n\n{neg_html}\n\nBegin by asking your first question."
        ),
        num_questions=config.cross_ex_questions,
        on_event=on_event,
    )
    html = f"<h2>1AC Cross-Examination of the 1NC</h2>\n{_format_aff_asks(pairs)}"
    return html, pairs


def cross_examine_2ac(config, debate_case, neg_html, twoac_html, on_event=None):
    """1NC cross-examines the 2AC. Returns (html, pairs)."""
    pairs = run_cross_examination(
        config=config,
        questioner_prompt=sp.cx_neg_questions_2ac(),
        responder_prompt=sp.cx_aff_answers_2ac(),
        summary_prompt=sp.cx_summary("1NC cross-examination of the 2AC"),
        response_model=CrossExNegAsks,
        context_message=(
            f"The 1AC is:\n\n{debate_case}\n\n"
            f"The 1NC is:\n\n{neg_html}\n\n"
            f"The 2AC is:\n\n{twoac_html}\n\nBegin by asking your first question."
        ),
        num_questions=config.cross_ex_questions,
        on_event=on_event,
    )
    html = f"<h2>1NC Cross-Examination of the 2AC</h2>\n{_format_neg_asks(pairs)}"
    return html, pairs


def cross_examine_2nc(config, debate_case, neg_html, twoac_html, twonc_html, on_event=None):
    """2AC cross-examines the 2NC. Returns (html, pairs)."""
    pairs = run_cross_examination(
        config=config,
        questioner_prompt=sp.cx_aff_questions_2nc(),
        responder_prompt=sp.cx_neg_answers_2nc(),
        summary_prompt=sp.cx_summary("2AC cross-examination of the 2NC"),
        response_model=CrossExAffAsks,
        context_message=(
            f"The 1AC is:\n\n{debate_case}\n\n"
            f"The 1NC is:\n\n{neg_html}\n\n"
            f"The 2AC is:\n\n{twoac_html}\n\n"
            f"The 2NC is:\n\n{twonc_html}\n\nBegin by asking your first question."
        ),
        num_questions=config.cross_ex_questions,
        on_event=on_event,
    )
    html = f"<h2>2AC Cross-Examination of the 2NC</h2>\n{_format_aff_asks(pairs)}"
    return html, pairs
