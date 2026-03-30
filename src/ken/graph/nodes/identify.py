import logging

from langchain_core.runnables import RunnableConfig

from ken.graph.context import NodeContext, build_choice
from ken.graph.state import AgentState
from ken.llm.prompts import LINK_SNIPER_SYSTEM, LINK_SNIPER_USER

logger = logging.getLogger(__name__)


def identify_node(state: AgentState, config: RunnableConfig) -> dict:
    """Use LLM to identify supplementary data links from the scraped markdown."""
    from ken.llm.client import LLMClient

    ctx = NodeContext(state, config)

    if state.get("error"):
        return {}

    ctx.update_status(":link: Identifying supplementary data links...")

    client = LLMClient(api_key=ctx.settings.anthropic_api_key, model=ctx.settings.llm_model)
    user_prompt = LINK_SNIPER_USER.format(
        page_url=state["page_url"],
        page_markdown=state["page_markdown"][:50000],
    )

    try:
        links = client.invoke_json(LINK_SNIPER_SYSTEM, user_prompt)
    except Exception as e:
        logger.exception("LLM link identification failed")
        return {"error": f"Failed to identify supplementary links: {e}", "status": "error"}

    if not isinstance(links, list):
        return {"error": "LLM returned unexpected format (not a list)", "status": "error"}

    data_links = [l for l in links if not l.get("is_external_reference")]
    external_links = [l for l in links if l.get("is_external_reference")]

    if not data_links and not external_links:
        return {"error": "No supplementary data links found on this page.", "status": "error"}

    if not data_links and external_links:
        ext_info = "\n".join(
            f"- {l.get('label', 'Unknown')}: {l.get('url', 'N/A')}" for l in external_links
        )
        return {
            "error": f"All datasets reference other papers. Try again with those links:\n{ext_info}",
            "status": "error",
        }

    logger.info("Found %d data links, %d external refs", len(data_links), len(external_links))

    if len(data_links) > 1:
        items = []
        for i, link in enumerate(data_links):
            label = link.get("label", f"File {i + 1}")
            ftype = link.get("file_type", "unknown")
            desc = link.get("description", "")
            items.append((str(i), f"*{label}* ({ftype}) — {desc}"))

        return {
            "supplementary_links": data_links,
            "status": "identified",
            **build_choice("links", f":link: Found {len(data_links)} supplementary data files:", items),
        }

    return {"supplementary_links": data_links, "needs_user_choice": False, "status": "identified"}
