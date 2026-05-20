"""Shared utilities for graph nodes — config extraction and Slack updates."""

import logging

from langchain_core.runnables import RunnableConfig

from panda.graph.state import AgentState

logger = logging.getLogger(__name__)


class NodeContext:
    """Extracts common config/state needed by every node."""

    __slots__ = ("settings", "slack_client", "channel", "thread_ts", "status_ts")

    def __init__(self, state: AgentState, config: RunnableConfig):
        cfg = config["configurable"]
        self.settings = cfg.get("settings")
        self.slack_client = cfg.get("slack_client")
        self.channel = state.get("slack_channel")
        self.thread_ts = state.get("slack_thread_ts")
        self.status_ts = cfg.get("slack_status_ts")

    def update_status(self, text: str) -> None:
        """Update the Slack status message. Silently no-ops if Slack isn't configured."""
        if self.slack_client and self.channel and self.status_ts:
            try:
                self.slack_client.chat_update(
                    channel=self.channel, ts=self.status_ts, text=text
                )
            except Exception:
                logger.debug("Failed to update Slack status", exc_info=True)

    def post_message(self, text: str, blocks: list[dict] | None = None) -> None:
        """Post a new message in the Slack thread."""
        if self.slack_client and self.channel and self.thread_ts:
            try:
                kwargs = {"channel": self.channel, "thread_ts": self.thread_ts, "text": text}
                if blocks:
                    kwargs["blocks"] = blocks
                self.slack_client.chat_postMessage(**kwargs)
            except Exception:
                logger.debug("Failed to post Slack message", exc_info=True)


def build_choice(
    context: str,
    header: str,
    items: list[tuple[str, str]],
    extra: dict | None = None,
) -> dict:
    """Build a standardized disambiguation return dict.

    Args:
        context: "links", "files", or "sheets"
        header: intro line (e.g., "Found 3 supplementary data files:")
        items: list of (id, display_line) tuples
        extra: additional state keys to include in the return
    """
    prompt_lines = [header]
    options = []
    for item_id, display in items:
        prompt_lines.append(display)
        options.append({"id": item_id, "label": display[:75]})

    result = {
        "needs_user_choice": True,
        "choice_context": context,
        "choice_prompt": "\n".join(prompt_lines),
        "choice_options": options,
    }
    if extra:
        result.update(extra)
    return result
