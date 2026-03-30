"""Slack Block Kit message builders."""


def status_message(text: str) -> list[dict]:
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]


def choice_message(prompt: str, options: list[dict]) -> list[dict]:
    """Build a message with buttons for user disambiguation.

    options: [{id: str, label: str}]
    """
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": prompt}}]

    buttons = []
    for opt in options:
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": opt["label"][:75]},
            "action_id": f"ken_choice_{opt['id']}",
            "value": opt["id"],
        })

    # Add "All" button
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "All"},
        "action_id": "ken_choice_all",
        "value": "all",
    })

    blocks.append({"type": "actions", "elements": buttons[:25]})  # Slack limit
    return blocks


def preview_message(
    filename: str,
    preview_text: str,
    row_count: int,
    col_count: int,
    saved_path: str,
) -> list[dict]:
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":white_check_mark: *Done!* Saved: `{saved_path}`\n"
                    f"`{filename}` — {row_count:,} rows x {col_count} columns"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```\n{preview_text}\n```",
            },
        },
    ]


def error_message(text: str) -> list[dict]:
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f":x: {text}"},
        }
    ]
