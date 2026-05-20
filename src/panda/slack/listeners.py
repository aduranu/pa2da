import logging
import re
import threading

from slack_bolt import App

from panda.config import Settings

logger = logging.getLogger(__name__)

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s>]+", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s>|]+")


def extract_link(text: str) -> str | None:
    """Extract a DOI or URL from a Slack message."""
    doi_match = DOI_PATTERN.search(text)
    if doi_match:
        return doi_match.group(0)
    url_match = URL_PATTERN.search(text)
    if url_match:
        return url_match.group(0)
    return None


def _handle_paper_request(settings, client, say, text, channel, thread_ts, user):
    """Shared handler for both mentions and DMs."""
    link = extract_link(text)
    if not link:
        say(text="Send me a DOI or URL to a paper. Example: `10.1038/s41467-024-12345-6`", thread_ts=thread_ts)
        return

    result = client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=":mag: Scanning publisher page...")
    status_ts = result["ts"]

    threading.Thread(
        target=_run_graph,
        args=(settings, client, channel, thread_ts, status_ts, user, link),
        daemon=True,
    ).start()


def register_listeners(app: App, settings: Settings):

    @app.event("app_mention")
    def handle_mention(event, say, client):
        _handle_paper_request(
            settings, client, say,
            event.get("text", ""),
            event["channel"],
            event.get("thread_ts") or event["ts"],
            event.get("user", ""),
        )

    @app.event("message")
    def handle_dm(event, say, client):
        if event.get("channel_type") != "im" or event.get("bot_id") or event.get("subtype"):
            return
        _handle_paper_request(
            settings, client, say,
            event.get("text", ""),
            event["channel"],
            event.get("thread_ts") or event["ts"],
            event.get("user", ""),
        )

    @app.action(re.compile(r"^panda_choice_.*"))
    def handle_choice(ack, action, body, client):
        ack()
        channel = body["channel"]["id"]
        thread_ts = body["message"].get("thread_ts") or body["message"]["ts"]

        logger.info("User chose %s in thread %s", action["value"], thread_ts)

        threading.Thread(
            target=_resume_graph,
            args=(settings, client, channel, thread_ts, action["value"]),
            daemon=True,
        ).start()


def _run_graph(settings, client, channel, thread_ts, status_ts, user, link):
    from panda.graph.builder import get_graph

    logger.info("Starting graph for link=%s thread=%s", link, thread_ts)
    graph = get_graph()
    config = {
        "configurable": {
            "thread_id": thread_ts,
            "settings": settings,
            "slack_client": client,
            "slack_channel": channel,
            "slack_status_ts": status_ts,
        }
    }

    try:
        graph.invoke(
            {"doi_or_url": link, "slack_channel": channel, "slack_thread_ts": thread_ts, "slack_user": user},
            config=config,
        )
    except Exception:
        logger.exception("Graph failed for thread %s", thread_ts)
        client.chat_postMessage(
            channel=channel, thread_ts=thread_ts,
            text=":x: Something went wrong processing that paper. Please try again.",
        )


def _resume_graph(settings, client, channel, thread_ts, value):
    from langgraph.types import Command
    from panda.graph.builder import get_graph

    logger.info("Resuming graph for thread=%s with value=%s", thread_ts, value)
    graph = get_graph()
    config = {
        "configurable": {
            "thread_id": thread_ts,
            "settings": settings,
            "slack_client": client,
            "slack_channel": channel,
        }
    }

    try:
        graph.invoke(Command(resume=value), config=config)
    except Exception:
        logger.exception("Graph resume failed for thread %s", thread_ts)
        client.chat_postMessage(
            channel=channel, thread_ts=thread_ts, text=":x: Something went wrong. Please try again.",
        )
