"""Pydantic models for structured LLM outputs."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Evidence card models
# ---------------------------------------------------------------------------

class DebateCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    retagged_argument_as_read_outloud_in_the_debate_round: str


class SingleCardResult(BaseModel):
    cards: List[DebateCard] = Field(..., min_length=1, max_length=1)


class MultiCardResult(BaseModel):
    """For 2AC/2NC evidence gathering (multiple cards)."""
    cards: List[DebateCard] = Field(..., min_length=1, max_length=7)


# ---------------------------------------------------------------------------
# Topicality models
# ---------------------------------------------------------------------------

class TopicalityInterpretationCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    formalized_topicality_interpretation: str


class TopicalityInterpretationResult(BaseModel):
    cards: List[TopicalityInterpretationCard] = Field(..., min_length=1, max_length=1)


class TopicalityViolationCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    formalized_topicality_violation: str


class TopicalityViolationResult(BaseModel):
    cards: List[TopicalityViolationCard] = Field(..., min_length=1, max_length=1)


class TopicalityReasonCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    detailed_reasons_to_prefer_arguments_as_delivered_in_debate: List[str] = Field(
        ..., min_length=3, max_length=3
    )


class TopicalityReasonResult(BaseModel):
    cards: List[TopicalityReasonCard] = Field(..., min_length=1, max_length=1)


# ---------------------------------------------------------------------------
# Theory models
# ---------------------------------------------------------------------------

class TheoryInterpretationCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    formalized_theory_interpretation: str


class TheoryInterpretationResult(BaseModel):
    cards: List[TheoryInterpretationCard] = Field(..., min_length=1, max_length=1)


class TheoryViolationCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    formalized_theory_violation: str


class TheoryViolationResult(BaseModel):
    cards: List[TheoryViolationCard] = Field(..., min_length=1, max_length=1)


class TheoryReasonCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    detailed_reasons_to_prefer_arguments_as_delivered_in_debate: List[str] = Field(
        ..., min_length=3, max_length=3
    )


class TheoryReasonResult(BaseModel):
    cards: List[TheoryReasonCard] = Field(..., min_length=1, max_length=1)


# ---------------------------------------------------------------------------
# Counterplan model
# ---------------------------------------------------------------------------

class CounterplanCard(BaseModel):
    id: int
    cite: str
    include_in_case: Literal["include_it", "False"]
    reason_to_include: str
    counterplantext: str


class CounterplanResult(BaseModel):
    cards: List[CounterplanCard] = Field(..., min_length=1, max_length=1)


# ---------------------------------------------------------------------------
# Plantext generation
# ---------------------------------------------------------------------------

class PlantextReview(BaseModel):
    plantext: str
    rationale: str
    advice_for_next_search: str


# ---------------------------------------------------------------------------
# Advantage generation
# ---------------------------------------------------------------------------

class Advantage(BaseModel):
    title: str
    core_argument: str


class AdvantagesResult(BaseModel):
    advantages: List[Advantage] = Field(..., min_length=3, max_length=3)
    rationale: str
    advice_for_next_search: str


# ---------------------------------------------------------------------------
# Negative off-case positions
# ---------------------------------------------------------------------------

class OffCasePosition(BaseModel):
    """A single negative off-case position.

    The ``position_type`` tells the builder what evidence structure to use:

    - ``"topicality"`` — interpretation, violation, reasons to prefer
    - ``"theory"`` — interpretation, violation, reasons to prefer
    - ``"disadvantage"`` — uniqueness, link, internal link, impact
    - ``"counterplan"`` — text, solvency, net benefit (requires ``counterplan_text``)
    - ``"kritik"`` — link, impact, role of the ballot (requires ``alternative_text``)
    """

    position_type: Literal["topicality", "theory", "disadvantage", "counterplan", "kritik"]
    title: str
    core_argument_summary_as_spoken_outloud_in_debate_round: str
    counterplan_text: str = ""
    alternative_text: str = ""


class NegativePositions(BaseModel):
    """The negative's strategic selection of off-case positions.

    Up to 4 positions, any mix of types. The negative chooses what
    gives them the best chance to win — no mandatory types.
    """

    positions: List[OffCasePosition] = Field(..., min_length=1, max_length=4)
    rationale: str
    advice_for_next_search: str


# ---------------------------------------------------------------------------
# Cross-examination
# ---------------------------------------------------------------------------

class CrossExPairNegAsks(BaseModel):
    negative_question: str
    affirmative_response: str


class CrossExNegAsks(BaseModel):
    cross_ex: List[CrossExPairNegAsks]


class CrossExPairAffAsks(BaseModel):
    affirmative_question: str
    negative_response: str


class CrossExAffAsks(BaseModel):
    cross_ex: List[CrossExPairAffAsks]


# ---------------------------------------------------------------------------
# Helper dataclass for evidence results
# ---------------------------------------------------------------------------

class EvidenceResult:
    """Bundles a found evidence card with its metadata."""

    __slots__ = ("doc", "argument", "card_id")

    def __init__(self, doc: dict, argument: str, card_id: int):
        self.doc = doc
        self.argument = argument
        self.card_id = card_id
