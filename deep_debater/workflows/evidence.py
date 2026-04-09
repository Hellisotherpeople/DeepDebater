"""1AC construction: plantext, harms, inherency, advantages, solvency."""

from __future__ import annotations

import ast
import json
from typing import Callable

from deep_debater.agents import run_evidence_search, run_iterative_generation
from deep_debater.config import DebateConfig
from deep_debater.db import get_document_by_id
from deep_debater.models import (
    AdvantagesResult,
    EvidenceResult,
    PlantextReview,
    SingleCardResult,
)
from deep_debater.prompts import affirmative as prompts


def _parse_card(config: DebateConfig, result: dict, key: str = "retagged_argument_as_read_outloud_in_the_debate_round") -> EvidenceResult:
    card = result["cards"][0]
    doc = get_document_by_id(config.db_path, card["id"])
    argument = card.get(key, "")
    return EvidenceResult(doc=doc, argument=argument, card_id=card["id"])


# ---------------------------------------------------------------------------
# Plantext
# ---------------------------------------------------------------------------

def generate_plantext(config: DebateConfig, topic: str, on_event: Callable | None = None) -> str:
    result = run_iterative_generation(
        config=config,
        generator_prompt=prompts.plantext_generator(),
        reviewer_prompt=prompts.plantext_reviewer(),
        context_message=(
            f"Devise a generic plantext for the following debate topic, "
            f"using iterative literature review: {topic}"
        ),
        response_model=PlantextReview,
        max_iterations=config.plantext_search_iterations,
        on_event=on_event,
    )
    return result["plantext"]


# ---------------------------------------------------------------------------
# Harms
# ---------------------------------------------------------------------------

def find_harm_evidence(
    config: DebateConfig, plan_text: str, topic: str, on_event: Callable | None = None
) -> tuple[str, EvidenceResult]:
    """Returns (debate_case_html, evidence_result)."""
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.harm_evaluator(),
        eval_agent_prompt=prompts.harm_eval_agent(),
        context_message=(
            f'Debate Topic: "{topic}"\n'
            f'Plan: "{plan_text}"\n\n'
            "Assume that the current year is 2022.\n"
            "Find the best, most recent, and most plan-specific evidence of harms. "
            "When generating the retagged_argument, ensure it is long and detailed."
        ),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"<div><h2>Debate Topic</h2><p>{topic}</p>"
        f"<h2>Plan</h2><p>{plan_text}</p>"
        f"<h2>Harm Argument</h2><p>{ev.argument}</p>"
        f"<h2>Harm Evidence</h2>{ev.doc['markup']}</div>"
    )
    return html, ev


# ---------------------------------------------------------------------------
# Inherency
# ---------------------------------------------------------------------------

def find_inherency_evidence(
    config: DebateConfig, debate_case: str, on_event: Callable | None = None
) -> tuple[str, EvidenceResult]:
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.inherency_evaluator(),
        eval_agent_prompt=prompts.inherency_eval_agent(),
        context_message=(
            f"{debate_case}\n\n"
            "Assume that the current year is 2022.\n"
            "Find the best inherency evidence supporting the plan and harm above."
        ),
        response_model=SingleCardResult,
        max_iterations=1,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"<div><h2>Inherency Argument</h2><p>{ev.argument}</p>"
        f"<h2>Inherency Evidence</h2>{ev.doc['markup']}</div>"
    )
    return debate_case + "\n" + html, ev


# ---------------------------------------------------------------------------
# Advantages
# ---------------------------------------------------------------------------

def generate_advantages(
    config: DebateConfig, debate_case: str, on_event: Callable | None = None
) -> list[str]:
    result = run_iterative_generation(
        config=config,
        generator_prompt=prompts.advantage_generator(),
        reviewer_prompt=prompts.advantage_reviewer(),
        context_message=(
            f"Given the following debate case, generate {config.num_advantages} "
            f"distinct, well-supported advantages.\n{debate_case}"
        ),
        response_model=AdvantagesResult,
        max_iterations=1,
        on_event=on_event,
    )
    return [str(adv) for adv in result["advantages"]]


def _adv_context(debate_case: str, adv_num: str, evidence_type: str) -> str:
    return (
        f"{debate_case}\n\n"
        f"Assume that the current year is 2022.\n"
        f"Find the best {evidence_type} evidence for advantage {adv_num}. "
        f"Do NOT select evidence already in the debate case."
    )


def find_advantage_uniqueness(config, debate_case, adv_num, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.advantage_uniqueness_evaluator(adv_num),
        eval_agent_prompt=prompts.advantage_uniqueness_eval(adv_num),
        context_message=_adv_context(debate_case, adv_num, "uniqueness"),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"\n<h2>Advantage {adv_num} Uniqueness</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return debate_case + html, ev


def find_advantage_link(config, debate_case, adv_num, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.advantage_link_evaluator(adv_num),
        eval_agent_prompt=prompts.advantage_link_eval(adv_num),
        context_message=_adv_context(debate_case, adv_num, "link"),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"\n<h2>Advantage {adv_num} Link</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return debate_case + html, ev


def find_advantage_internal_link(config, debate_case, adv_num, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.advantage_internal_link_evaluator(adv_num),
        eval_agent_prompt=prompts.advantage_internal_link_eval(adv_num),
        context_message=_adv_context(debate_case, adv_num, "internal link"),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"\n<h2>Advantage {adv_num} Internal Link</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return debate_case + html, ev


def find_advantage_impact(config, debate_case, adv_num, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.advantage_impact_evaluator(adv_num),
        eval_agent_prompt=prompts.advantage_impact_eval(adv_num),
        context_message=_adv_context(debate_case, adv_num, "impact"),
        response_model=SingleCardResult,
        max_iterations=1,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"\n<h2>Advantage {adv_num} Impact</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<div><p>{ev.doc['markup']}</p></div>"
    )
    return debate_case + html, ev


# ---------------------------------------------------------------------------
# Solvency
# ---------------------------------------------------------------------------

def find_solvency_evidence(config, debate_case, on_event=None):
    result = run_evidence_search(
        config=config,
        evaluator_prompt=prompts.solvency_evaluator(),
        eval_agent_prompt=prompts.solvency_eval_agent(),
        context_message=(
            f"{debate_case}\n\n"
            "Find the best solvency evidence supporting the plan and the harm above. "
            "Do NOT select evidence already in the debate case."
        ),
        response_model=SingleCardResult,
        on_event=on_event,
    )
    ev = _parse_card(config, result)
    html = (
        f"\n<h2>Solvency Argument</h2>"
        f"\n<div><p>{ev.argument}</p></div>"
        f"\n<h2>Solvency Card</h2>"
        f"\n<div>{ev.doc['markup']}</div>"
    )
    return debate_case + html, ev


# ---------------------------------------------------------------------------
# Build full 1AC
# ---------------------------------------------------------------------------

def build_1ac(config: DebateConfig, topic: str, on_event: Callable | None = None) -> str:
    """Build the complete 1AC debate case. Returns the HTML string."""

    def _emit(msg):
        if on_event:
            on_event({"type": "step", "message": msg})

    def _retry(fn, *args, **kwargs):
        last_exc = None
        for attempt in range(config.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if attempt == config.max_retries - 1:
                    raise
        raise last_exc

    _emit("Generating plantext...")
    plantext = _retry(generate_plantext, config, topic, on_event)

    _emit("Finding harm evidence...")
    debate_case, harm_ev = _retry(find_harm_evidence, config, plantext, topic, on_event)

    _emit("Finding inherency evidence...")
    debate_case, inh_ev = _retry(find_inherency_evidence, config, debate_case, on_event)

    _emit("Generating advantages...")
    advantages = _retry(generate_advantages, config, debate_case, on_event)

    for i in range(config.num_advantages):
        adv_num = str(i + 1)
        adv_dict = json.loads(json.dumps(ast.literal_eval(advantages[i])))
        debate_case += (
            f"\n<h2>Advantage {adv_num}: {adv_dict['title']}</h2>"
            f"\n<div><p>{adv_dict['core_argument']}</p></div>"
        )

        _emit(f"Finding advantage {adv_num} uniqueness...")
        debate_case, _ = _retry(find_advantage_uniqueness, config, debate_case, adv_num, on_event)

        _emit(f"Finding advantage {adv_num} link...")
        debate_case, _ = _retry(find_advantage_link, config, debate_case, adv_num, on_event)

        _emit(f"Finding advantage {adv_num} internal link...")
        debate_case, _ = _retry(find_advantage_internal_link, config, debate_case, adv_num, on_event)

        _emit(f"Finding advantage {adv_num} impact...")
        debate_case, _ = _retry(find_advantage_impact, config, debate_case, adv_num, on_event)

    _emit("Finding solvency evidence...")
    debate_case, solv_ev = _retry(find_solvency_evidence, config, debate_case, on_event)

    return debate_case
