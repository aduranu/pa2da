import logging

from langchain_core.runnables import RunnableConfig

from panda.graph.context import NodeContext
from panda.graph.state import AgentState
from panda.slack.blocks import error_message, preview_message

logger = logging.getLogger(__name__)


def deliver_node(state: AgentState, config: RunnableConfig) -> dict:
    """Post results (or errors) to the Slack thread."""
    ctx = NodeContext(state, config)

    if not ctx.slack_client or not ctx.channel or not ctx.thread_ts:
        logger.warning("No Slack context available for delivery")
        return {"status": "delivered"}

    if state.get("error"):
        ctx.post_message(state["error"], error_message(state["error"]))
        return {"status": "delivered_error"}

    processed = state.get("processed_files", [])
    if not processed:
        ctx.post_message(":warning: Processing completed but no files were produced.")
        return {"status": "delivered_empty"}

    for pf in processed:
        if "error" in pf:
            ctx.post_message(
                pf["error"], error_message(f"Failed to process `{pf['filename']}`: {pf['error']}")
            )
            continue

        ctx.post_message(
            f"Done! Saved: {pf['path']}",
            preview_message(
                filename=pf["filename"],
                preview_text=pf["preview_text"],
                row_count=pf["row_count"],
                col_count=pf["col_count"],
                saved_path=pf["path"],
            ),
        )

    return {"status": "delivered"}
