"""Reusable agent workflow patterns.

Uses AG2 (``ag2`` package, version >=0.6,<1.0) which provides the classic
``autogen`` API: ``ConversableAgent``, ``GroupChat``, ``GroupChatManager``,
``LLMConfig``, ``register_function``.

The four factory functions here collapse ~40 nearly-identical agent
workflows from the original notebook into composable building blocks.
"""

from __future__ import annotations

import json
from typing import Callable

from autogen import Agent, ConversableAgent, GroupChat, GroupChatManager, register_function
from pydantic import BaseModel

from deep_debater.config import DebateConfig
from deep_debater.db import make_search_fn

DEFAULT_SEARCH_PROMPT = (
    "You are a helpful assistant that can search the debate evidence dataset "
    "for a given tag or query. Your query will retrieve a list of debate cards."
)


def _extract_json(chat_result) -> dict:
    """Parse JSON from the last message of a chat result."""
    return json.loads(chat_result.chat_history[-1]["content"])


# ------------------------------------------------------------------
# 1) Evidence search
# ------------------------------------------------------------------

def run_evidence_search(
    config: DebateConfig,
    evaluator_prompt: str,
    eval_agent_prompt: str,
    context_message: str,
    response_model: type[BaseModel],
    *,
    search_agent_prompt: str = DEFAULT_SEARCH_PROMPT,
    max_iterations: int = 3,
    max_rounds: int = 40,
    on_event: Callable | None = None,
) -> dict:
    """Universal evidence-finding workflow.

    Creates a 4-agent GroupChat (evaluator -> search -> executor -> eval),
    runs it, and returns the parsed JSON output.

    This single function replaces ~25 nearly-identical functions from the
    original notebook.
    """
    llm = config.base_llm()
    required_llm = config.required_llm()
    eval_llm = config.structured_llm(response_model)

    argument_evaluator = ConversableAgent(
        name="argument_evaluator",
        system_message=evaluator_prompt,
        llm_config=llm,
    )
    debate_search_agent = ConversableAgent(
        name="debate_search_agent",
        system_message=search_agent_prompt,
        llm_config=required_llm,
    )
    executor_agent = ConversableAgent(
        name="executor_agent",
        human_input_mode="NEVER",
        llm_config=llm,
    )
    debate_eval_agent = ConversableAgent(
        name="debate_eval_agent",
        system_message=eval_agent_prompt,
        llm_config=eval_llm,
    )

    search_fn = make_search_fn(config.db_path)
    register_function(
        search_fn,
        caller=debate_search_agent,
        executor=executor_agent,
        description="Search the debate evidence dataset using natural language queries. Return a list of debate cards.",
    )

    iterations = 0

    def speaker_selection(last_speaker: Agent, groupchat: GroupChat):
        nonlocal iterations
        messages = groupchat.messages
        if len(messages) <= 1:
            return argument_evaluator
        if last_speaker is debate_search_agent:
            return executor_agent
        if last_speaker is executor_agent:
            return debate_eval_agent
        if last_speaker is debate_eval_agent:
            if "include_it" in messages[-1].get("content", ""):
                iterations += 1
                if on_event:
                    on_event({"type": "evidence_found", "iteration": iterations})
                if iterations >= max_iterations:
                    return None
            return debate_search_agent
        if last_speaker is argument_evaluator:
            return debate_search_agent
        return "round_robin"

    group_chat = GroupChat(
        agents=[argument_evaluator, debate_search_agent, executor_agent, debate_eval_agent],
        messages=[],
        max_round=max_rounds,
        speaker_selection_method=speaker_selection,
    )
    manager = GroupChatManager(groupchat=group_chat, llm_config=llm)
    chat_result = argument_evaluator.initiate_chat(
        manager, message=context_message, silent=True,
    )
    return _extract_json(chat_result)


# ------------------------------------------------------------------
# 2) Iterative generation
# ------------------------------------------------------------------

def run_iterative_generation(
    config: DebateConfig,
    generator_prompt: str,
    reviewer_prompt: str,
    context_message: str,
    response_model: type[BaseModel],
    *,
    max_iterations: int = 4,
    max_rounds: int = 50,
    on_event: Callable | None = None,
) -> dict:
    """Iterative search-and-refine workflow.

    Pattern: generator -> search -> executor -> reviewer -> (loop).
    Used for plantext, advantage, and negative-position generation.
    """
    llm = config.base_llm()
    required_llm = config.required_llm()
    eval_llm = config.structured_llm(response_model)

    generator = ConversableAgent(
        name="generator",
        system_message=generator_prompt,
        llm_config=llm,
    )
    debate_search_agent = ConversableAgent(
        name="debate_search_agent",
        system_message=DEFAULT_SEARCH_PROMPT,
        llm_config=required_llm,
    )
    executor_agent = ConversableAgent(
        name="executor_agent",
        human_input_mode="NEVER",
        llm_config=llm,
    )
    reviewer = ConversableAgent(
        name="reviewer",
        system_message=reviewer_prompt,
        llm_config=eval_llm,
    )

    search_fn = make_search_fn(config.db_path)
    register_function(
        search_fn,
        caller=debate_search_agent,
        executor=executor_agent,
        description="Search the debate evidence dataset using natural language queries. Return a list of debate cards.",
    )

    iterations = 0

    def speaker_selection(last_speaker: Agent, groupchat: GroupChat):
        nonlocal iterations
        messages = groupchat.messages
        if len(messages) == 0:
            return generator
        if last_speaker is generator:
            return debate_search_agent
        if last_speaker is debate_search_agent:
            return executor_agent
        if last_speaker is executor_agent:
            return reviewer
        if last_speaker is reviewer:
            iterations += 1
            if on_event:
                on_event({"type": "iteration", "count": iterations})
            if iterations >= max_iterations:
                return None
            return debate_search_agent
        return "round_robin"

    group_chat = GroupChat(
        agents=[generator, debate_search_agent, executor_agent, reviewer],
        messages=[],
        max_round=max_rounds,
        speaker_selection_method=speaker_selection,
    )
    manager = GroupChatManager(groupchat=group_chat, llm_config=llm)
    chat_result = generator.initiate_chat(
        manager, message=context_message, silent=True,
    )
    return _extract_json(chat_result)


# ------------------------------------------------------------------
# 3) Speech drafting
# ------------------------------------------------------------------

def run_speech_draft(
    config: DebateConfig,
    drafter_prompt: str,
    coach_prompt: str,
    context_message: str,
    *,
    max_rounds: int = 4,
    on_event: Callable | None = None,
) -> str:
    """Draft-and-review speech writing workflow.

    Returns the final transcript string.
    """
    llm = config.base_llm()

    drafter = ConversableAgent(
        name="drafter",
        system_message=drafter_prompt,
        llm_config=llm,
    )
    coach = ConversableAgent(
        name="coach",
        system_message=coach_prompt,
        llm_config=llm,
    )

    def speaker_selection(last_speaker, groupchat):
        if len(groupchat.messages) == 0:
            return drafter
        if last_speaker is drafter:
            return None  # terminate after first draft
        if last_speaker is coach:
            return drafter
        return None

    group_chat = GroupChat(
        agents=[drafter, coach],
        messages=[],
        max_round=max_rounds,
        speaker_selection_method=speaker_selection,
    )
    manager = GroupChatManager(groupchat=group_chat, llm_config=llm)
    chat_result = coach.initiate_chat(
        manager, message=context_message, silent=True,
    )

    if on_event:
        on_event({"type": "speech_drafted"})

    # Return the last message content (the drafter's output)
    return chat_result.chat_history[-1]["content"]


# ------------------------------------------------------------------
# 4) Cross-examination
# ------------------------------------------------------------------

def run_cross_examination(
    config: DebateConfig,
    questioner_prompt: str,
    responder_prompt: str,
    summary_prompt: str,
    response_model: type[BaseModel],
    context_message: str,
    *,
    num_questions: int = 4,
    on_event: Callable | None = None,
) -> list[dict]:
    """Cross-examination workflow.

    Returns list of Q&A pair dicts.
    """
    llm = config.base_llm()
    cx_llm = config.structured_llm(response_model)

    questioner = ConversableAgent(
        name="questioner",
        system_message=questioner_prompt,
        llm_config=llm,
    )
    responder = ConversableAgent(
        name="responder",
        system_message=responder_prompt,
        llm_config=llm,
    )
    summary_agent = ConversableAgent(
        name="summary_agent",
        system_message=summary_prompt,
        llm_config=cx_llm,
    )

    cx_iterations = 0

    def speaker_selection(last_speaker, groupchat):
        nonlocal cx_iterations
        if cx_iterations == 0 and last_speaker is None:
            return questioner
        if last_speaker is questioner:
            return responder
        if last_speaker is responder:
            cx_iterations += 1
            if cx_iterations >= num_questions:
                return summary_agent
            return questioner
        if last_speaker is summary_agent:
            return None
        return "round_robin"

    group_chat = GroupChat(
        agents=[questioner, responder, summary_agent],
        messages=[],
        max_round=num_questions * 3 + 5,
        speaker_selection_method=speaker_selection,
    )
    manager = GroupChatManager(groupchat=group_chat, llm_config=llm)
    chat_result = responder.initiate_chat(
        manager, message=context_message, silent=True,
    )

    if on_event:
        on_event({"type": "cross_ex_complete"})

    raw = json.loads(chat_result.chat_history[-1]["content"])
    return raw["cross_ex"]
