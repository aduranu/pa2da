import logging
import os

from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from panda.graph.context import NodeContext
from panda.graph.state import AgentState
from panda.slack.blocks import choice_message

logger = logging.getLogger(__name__)


def disambiguate_node(state: AgentState, config: RunnableConfig) -> dict:
    """Pause the graph and ask the user to choose. Resumes when user clicks a button."""
    ctx = NodeContext(state, config)

    prompt = state.get("choice_prompt", "Please choose:")
    options = state.get("choice_options", [])

    ctx.post_message(prompt, choice_message(prompt, options))

    # Pause — resumes when user clicks a button
    user_choice = interrupt({"prompt": prompt, "options": options})
    context = state.get("choice_context", "links")

    logger.info("User chose: %s (context: %s)", user_choice, context)

    result: dict = {"user_choice": user_choice, "needs_user_choice": False}

    if context == "links":
        links = state.get("supplementary_links", [])
        result["supplementary_links"] = links if user_choice == "all" else [links[int(user_choice)]]

    elif context == "files":
        files = state.get("downloaded_files", [])
        if user_choice == "all":
            result["downloaded_files"] = files
        else:
            result["downloaded_files"] = [f for f in files if f["original_name"] == user_choice]

    # "sheets" context: user_choice is the sheet name, process node reads it directly

    return result
