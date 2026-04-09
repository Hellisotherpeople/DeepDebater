"""1NC construction: off-case positions, topicality, theory, DA, CP, K, on-case."""

from __future__ import annotations

import json
from typing import Callable

from deep_debater.agents import run_evidence_search, run_iterative_generation
from deep_debater.config import DebateConfig
from deep_debater.db import get_document_by_id
from deep_debater.models import (
    CounterplanResult,
    EvidenceResult,
    NegativePositions,
    SingleCardResult,
    TheoryInterpretationResult,
    TheoryReasonResult,
    TheoryViolationResult,
    TopicalityInterpretationResult,
    TopicalityReasonResult,
    TopicalityViolationResult,
)
from deep_debater.prompts import negative as prompts


def _parse_card(config, result, key="retagged_argument_as_read_outloud_in_the_debate_round"):
    card = result["cards"][0]
    doc = get_document_by_id(config.db_path, card["id"])
    return EvidenceResult(doc=doc, argument=card.get(key, ""), card_id=card["id"])


def _neg_ctx(debate_case, neg_html, extra=""):
    return f"{debate_case}\n\n{neg_html}\n\nAssume that the current year is 2022.\n{extra}"


# ---------------------------------------------------------------------------
# Off-case generation
# ---------------------------------------------------------------------------

def generate_negative_offcase(config, debate_case, on_event=None) -> dict:
    result = run_iterative_generation(
        config=config,
        generator_prompt=prompts.neg_offcase_generator(),
        reviewer_prompt=prompts.neg_offcase_reviewer(),
        context_message=(
            f"Given the following affirmative debate case, generate negative "
            f"off-case positions.\n{debate_case}"
        ),
        response_model=NegativePositions,
        max_iterations=3,
        on_event=on_event,
    )
    return result


def extract_titles(negative_case: dict) -> list[str]:
    titles = []
    for key in ("topicality", "theory"):
        if key in negative_case and negative_case[key]:
            titles.append(negative_case[key]["title"])
    for key in ("disadvantages", "counterplans", "kritiks"):
        for item in negative_case.get(key, []):
            titles.append(item["title"])
    return titles


# ---------------------------------------------------------------------------
# Topicality
# ---------------------------------------------------------------------------

def add_topicality_interpretation(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.topicality_interpretation_evaluator(),
        eval_agent_prompt=prompts.topicality_interpretation_eval(),
        context_message=_neg_ctx(debate_case, neg_html,
            "Formulate a formalized topicality interpretation and find supporting evidence."),
        response_model=TopicalityInterpretationResult,
        on_event=on_event,
    )
    card = result["cards"][0]
    interp = card.get("formalized_topicality_interpretation", "")
    doc = get_document_by_id(config.db_path, card["id"])
    neg_html += (
        f"\n<h2>Topicality Interpretation and Evidence</h2>"
        f"\n<div><p>{interp}</p></div>"
        f"\n<div><p>{doc['markup']}</p></div>"
    )
    return neg_html, interp, doc


def add_topicality_violation(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.topicality_violation_evaluator(),
        eval_agent_prompt=prompts.topicality_violation_eval(),
        context_message=_neg_ctx(debate_case, neg_html,
            "Formulate a formalized topicality violation."),
        response_model=TopicalityViolationResult,
        on_event=on_event,
    )
    violation = result["cards"][0].get("formalized_topicality_violation", "")
    neg_html += f"\n<h2>Topicality Violation</h2>\n<div><p>{violation}</p></div>"
    return neg_html, violation


def add_topicality_reasons_to_prefer(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.topicality_reasons_evaluator(),
        eval_agent_prompt=prompts.topicality_reasons_eval(),
        context_message=_neg_ctx(debate_case, neg_html,
            "Generate three reasons to prefer the negative's interpretation."),
        response_model=TopicalityReasonResult,
        on_event=on_event,
    )
    reasons = result["cards"][0].get(
        "detailed_reasons_to_prefer_arguments_as_delivered_in_debate", []
    )
    items = "".join(f"<li>{r}</li>" for r in reasons)
    neg_html += f"\n<h2>Topicality Reasons to Prefer</h2>\n<div><ol>{items}</ol></div>"
    return neg_html, reasons


# ---------------------------------------------------------------------------
# Theory
# ---------------------------------------------------------------------------

def add_theory_interpretation(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.theory_interpretation_evaluator(),
        eval_agent_prompt=prompts.theory_interpretation_eval(),
        context_message=_neg_ctx(debate_case, neg_html,
            "Formulate a formalized theory interpretation and find supporting evidence."),
        response_model=TheoryInterpretationResult,
        on_event=on_event,
    )
    card = result["cards"][0]
    interp = card.get("formalized_theory_interpretation", "")
    doc = get_document_by_id(config.db_path, card["id"])
    neg_html += (
        f"\n<h2>Theory Interpretation and Evidence</h2>"
        f"\n<div><p>{interp}</p></div>"
        f"\n<div><p>{doc['markup']}</p></div>"
    )
    return neg_html, interp, doc


def add_theory_violation(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.theory_violation_evaluator(),
        eval_agent_prompt=prompts.theory_violation_eval(),
        context_message=_neg_ctx(debate_case, neg_html,
            "Formulate a formalized theory violation argument."),
        response_model=TheoryViolationResult,
        on_event=on_event,
    )
    violation = result["cards"][0].get("formalized_theory_violation", "")
    neg_html += f"\n<h2>Theory Violation Argument</h2>\n<div><p>{violation}</p></div>"
    return neg_html, violation


def add_theory_reasons_to_prefer(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.theory_reasons_evaluator(),
        eval_agent_prompt=prompts.theory_reasons_eval(),
        context_message=_neg_ctx(debate_case, neg_html,
            "Generate three reasons to prefer the negative's theory interpretation."),
        response_model=TheoryReasonResult,
        on_event=on_event,
    )
    reasons = result["cards"][0].get(
        "detailed_reasons_to_prefer_arguments_as_delivered_in_debate", []
    )
    items = "".join(f"<li>{r}</li>" for r in reasons)
    neg_html += f"\n<h2>Theory Reasons to Prefer</h2>\n<div><ol>{items}</ol></div>"
    return neg_html, reasons


# ---------------------------------------------------------------------------
# Disadvantage
# ---------------------------------------------------------------------------

def _da_ctx(debate_case, neg_html, extra):
    return f"{debate_case}\n\n{neg_html}\n\nAssume that the current year is 2022.\n{extra}"


def add_da_uniqueness(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.da_uniqueness_evaluator(),
        eval_agent_prompt=prompts.da_uniqueness_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best disadvantage uniqueness evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Disadvantage Uniqueness</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


def add_da_link(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.da_link_evaluator(),
        eval_agent_prompt=prompts.da_link_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best disadvantage link evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Disadvantage Link</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


def add_da_internal_link(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.da_internal_link_evaluator(),
        eval_agent_prompt=prompts.da_internal_link_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best disadvantage internal link evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Disadvantage Internal Link</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


def add_da_impact(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.da_impact_evaluator(),
        eval_agent_prompt=prompts.da_impact_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best disadvantage impact evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Disadvantage Impact</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


# ---------------------------------------------------------------------------
# Counterplan
# ---------------------------------------------------------------------------

def add_cp_text(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.cp_text_evaluator(),
        eval_agent_prompt=prompts.cp_text_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best counterplan text."),
        response_model=CounterplanResult,
        on_event=on_event,
    )
    cp_text = result["cards"][0].get("counterplantext", "")
    neg_html += f"\n<h2>Counterplan Text</h2>\n<div><p>{cp_text}</p></div>"
    return neg_html, cp_text


def add_cp_solvency(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.cp_solvency_evaluator(),
        eval_agent_prompt=prompts.cp_solvency_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best counterplan solvency evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Counterplan Solvency</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


def add_cp_net_benefit(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.cp_net_benefit_evaluator(),
        eval_agent_prompt=prompts.cp_net_benefit_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best counterplan net benefit evidence."),
        response_model=SingleCardResult,
        max_iterations=1,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Counterplan Net Benefit</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


# ---------------------------------------------------------------------------
# Kritik
# ---------------------------------------------------------------------------

def add_kritik_link(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.kritik_link_evaluator(),
        eval_agent_prompt=prompts.kritik_link_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best kritik link evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Kritik Link</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


def add_kritik_impact(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.kritik_impact_evaluator(),
        eval_agent_prompt=prompts.kritik_impact_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best kritik impact evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Kritik Impact</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


def add_kritik_rotb(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.kritik_rotb_evaluator(),
        eval_agent_prompt=prompts.kritik_rotb_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best kritik role of the ballot evidence."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>Kritik Role of the Ballot</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


# ---------------------------------------------------------------------------
# On-case rebuttal
# ---------------------------------------------------------------------------

def add_on_case_rebuttal(config, debate_case, neg_html, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.on_case_evaluator(),
        eval_agent_prompt=prompts.on_case_eval(),
        context_message=_da_ctx(debate_case, neg_html,
            "Find the best on-case rebuttal evidence. "
            "Do NOT select a card already refuted."),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    neg_html += (
        f"\n<h2>On-Case Rebuttal</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return neg_html, ev


# ---------------------------------------------------------------------------
# Build full 1NC
# ---------------------------------------------------------------------------

def build_1nc(config: DebateConfig, debate_case: str, on_event: Callable | None = None) -> tuple[str, dict]:
    """Build the complete 1NC. Returns (negative_case_html, negative_positions_dict)."""

    def _emit(msg):
        if on_event:
            on_event({"type": "step", "message": msg})

    def _retry(fn, *args, **kwargs):
        last_exc = None
        for _ in range(config.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
        raise last_exc

    _emit("Generating negative off-case positions...")
    neg_case = _retry(generate_negative_offcase, config, debate_case, on_event)
    neg_html = ""

    # Topicality
    t = neg_case.get("topicality", {})
    if t and t.get("title"):
        _emit("Building topicality...")
        neg_html += f"<h2>{t['title']}</h2>\n<p>{t.get('core_argument_summary_as_spoken_outloud_in_debate_round', '')}</p>"
        neg_html, _, _ = _retry(add_topicality_interpretation, config, debate_case, neg_html, on_event)
        neg_html, _ = _retry(add_topicality_violation, config, debate_case, neg_html, on_event)
        neg_html, _ = _retry(add_topicality_reasons_to_prefer, config, debate_case, neg_html, on_event)

    # Theory
    th = neg_case.get("theory", {})
    if th and th.get("title"):
        _emit("Building theory...")
        neg_html += f"<h2>{th['title']}</h2>\n<p>{th.get('core_argument_summary_as_spoken_outloud_in_debate_round', '')}</p>"
        neg_html, _, _ = _retry(add_theory_interpretation, config, debate_case, neg_html, on_event)
        neg_html, _ = _retry(add_theory_violation, config, debate_case, neg_html, on_event)
        neg_html, _ = _retry(add_theory_reasons_to_prefer, config, debate_case, neg_html, on_event)

    # Disadvantage
    da = neg_case["disadvantages"][0]
    _emit("Building disadvantage...")
    neg_html += f"<h2>{da['title']}</h2>\n<p>{da.get('core_argument_summary_as_spoken_outloud_in_debate_round', '')}</p>"
    neg_html, _ = _retry(add_da_uniqueness, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_da_link, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_da_internal_link, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_da_impact, config, debate_case, neg_html, on_event)

    # Counterplan
    _emit("Building counterplan...")
    neg_html, _ = _retry(add_cp_text, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_cp_solvency, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_cp_net_benefit, config, debate_case, neg_html, on_event)

    # Kritik
    k = neg_case["kritiks"][0]
    _emit("Building kritik...")
    neg_html += (
        f"<h2>{k['title']}</h2>\n"
        f"<p>{k.get('core_argument_summary_as_spoken_outloud_in_debate_round', '')}</p>\n"
        f"<p><strong>Thus the Alternative:</strong> {k.get('alternative_text', '')}</p>"
    )
    neg_html, _ = _retry(add_kritik_link, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_kritik_impact, config, debate_case, neg_html, on_event)
    neg_html, _ = _retry(add_kritik_rotb, config, debate_case, neg_html, on_event)

    # On-case rebuttals
    _emit("Building on-case rebuttals...")
    for _ in range(config.on_case_rebuttals):
        neg_html, _ = _retry(add_on_case_rebuttal, config, debate_case, neg_html, on_event)

    return neg_html, neg_case
