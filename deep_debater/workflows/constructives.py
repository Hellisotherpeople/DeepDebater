"""2AC and 2NC evidence gathering and speech writing."""

from __future__ import annotations

import json
from typing import Callable

from deep_debater.agents import run_evidence_search, run_speech_draft
from deep_debater.config import DebateConfig
from deep_debater.db import get_document_by_id
from deep_debater.models import MultiCardResult
from deep_debater.prompts import speeches as sp


def _gather_evidence(config, context_message, side_prompt, eval_prompt, on_event=None):
    """Shared evidence-gathering logic for 2AC/2NC."""
    result = run_evidence_search(
        config=config,
        evaluator_prompt=side_prompt,
        eval_agent_prompt=eval_prompt,
        context_message=context_message,
        response_model=MultiCardResult,
        max_iterations=3,
        max_rounds=60,
        on_event=on_event,
    )
    cards = result["cards"]
    html = ""
    for idx, card_json in enumerate(cards):
        doc = get_document_by_id(config.db_path, card_json["id"])
        arg = card_json.get("retagged_argument_as_read_outloud_in_the_debate_round", "")
        html += (
            f"\n<h2>Card {idx+1}</h2>"
            f"\n<div><p>{arg}</p></div>"
            f"\n<div><p>{doc['markup']}</p></div>"
        )
    return html, cards


# ---------------------------------------------------------------------------
# 2AC
# ---------------------------------------------------------------------------

_2AC_EVALUATOR = (
    "You are an expert affirmative policy debater preparing the 2AC. "
    "Identify which 1NC arguments the 1AC is most vulnerable to and select "
    "the most strategic, high-quality, unique cards that directly answer those "
    "arguments. Every card must support the affirmative position. "
    "Do NOT select any card already in the 1AC or 1NC."
)

_2AC_EVAL = (
    "Strictly evaluate whether each proposed 2AC card is directly responsive "
    "to a threatening 1NC argument, unique, authoritative, and supportive of "
    "the affirmative. Reject duplicates and cards already in the 1AC or 1NC."
)


def gather_2ac_evidence(config, debate_case, neg_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        "Assume that the current year is 2022.\n"
        "Select the most strategic 2AC cards to answer the 1NC's most dangerous arguments."
    )
    html, cards = _gather_evidence(config, ctx, _2AC_EVALUATOR, _2AC_EVAL, on_event)
    return f"<div class='two-ac-section'>\n<h1>2AC</h1>\n{html}\n</div>", cards


def write_2ac_speech(config, debate_case, neg_html, twoac_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC Cards:\n{twoac_html}\n\n"
        "Write a complete, realistic 2AC speech transcript."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.twoac_drafter(),
        coach_prompt=sp.twoac_coach(),
        context_message=ctx,
        on_event=on_event,
    )
    full_html = twoac_html + f"\n<div class='two-ac-section'><h1>2AC Speech</h1>"
    full_html += f"<div class='twoac-transcript'>{transcript}</div></div>"
    return full_html, transcript


# ---------------------------------------------------------------------------
# 2NC
# ---------------------------------------------------------------------------

_2NC_EVALUATOR = (
    "You are an expert negative policy debater preparing the 2NC. "
    "Identify which 2AC arguments are most threatening and select the most "
    "strategic cards to answer them. Every card must support the negative. "
    "Do NOT select any card already in the 1AC, 1NC, or 2AC."
)

_2NC_EVAL = (
    "Strictly evaluate whether each proposed 2NC card is directly responsive "
    "to a threatening 2AC argument, unique, authoritative, and supportive of "
    "the negative. Reject duplicates and cards already used."
)


def gather_2nc_evidence(config, debate_case, neg_html, twoac_html, on_event=None):
    ctx = (
        f"Negative Case (1NC) (Our Team):\n{neg_html}\n\n"
        f"Affirmative Case (1AC):\n{debate_case}\n\n"
        f"2AC:\n{twoac_html}\n\n"
        "Assume that the current year is 2022.\n"
        "Select the most strategic 2NC cards."
    )
    html, cards = _gather_evidence(config, ctx, _2NC_EVALUATOR, _2NC_EVAL, on_event)
    return f"<div class='two-nc-section'>\n<h1>2NC</h1>\n{html}\n</div>", cards


def write_2nc_speech(config, debate_case, neg_html, twoac_html, twonc_html, on_event=None):
    ctx = (
        f"{debate_case}\n\nNegative Case (1NC):\n{neg_html}\n\n"
        f"2AC:\n{twoac_html}\n\n2NC Cards:\n{twonc_html}\n\n"
        "Write a complete, realistic 2NC speech transcript."
    )
    transcript = run_speech_draft(
        config=config,
        drafter_prompt=sp.twonc_drafter(),
        coach_prompt=sp.twonc_coach(),
        context_message=ctx,
        on_event=on_event,
    )
    full_html = twonc_html + f"\n<div class='two-nc-speech-section'><h1>2NC Speech</h1>"
    full_html += f"<div class='two-nc-transcript'>{transcript}</div></div>"
    return full_html, transcript
