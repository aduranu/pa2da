from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Input
    doi_or_url: str
    slack_channel: str
    slack_thread_ts: str
    slack_user: str

    # Scrape
    page_markdown: str
    page_url: str  # resolved canonical URL

    # Identify
    supplementary_links: list[dict]  # [{url, label, file_type, description, is_external_reference}]

    # Disambiguate
    needs_user_choice: bool
    choice_context: str  # "links" or "files" or "sheets" — where to route after choice
    choice_prompt: str
    choice_options: list[dict]  # [{id, label}]
    user_choice: str | None

    # Download
    downloaded_files: list[dict]  # [{local_path, original_name, mime_type}]

    # Process
    processed_files: list[dict]  # [{path, preview_text, row_count, col_count, filename}]

    # Control
    error: str | None
    status: str
