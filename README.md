Panda Data Agent

Slack bot that pulls supplementary data from scientific papers. Drop a DOI or URL, get back cleaned Excel/CSV.

Setup

1. Install deps (requires Python 3.11+ and uv):

   uv sync

2. Copy .env.example to .env and fill in:

   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   SLACK_SIGNING_SECRET=...
   FIRECRAWL_API_KEY=...
   ANTHROPIC_API_KEY=...
   JINA_API_KEY=         # optional fallback scraper

3. In your Slack app config, enable Socket Mode and subscribe the bot to:
   - app_mention
   - message.im

Run

   uv run panda

Test the MVP

In Slack, either DM the bot or @-mention it in a channel where it's invited, with a paper link:

   @panda https://www.nature.com/articles/s41467-024-12345-6
   @panda 10.1038/s41467-024-12345-6

The bot will:
1. Scrape the paper page
2. List supplementary files it found and ask you to pick one (interactive button)
3. Download, clean, and save the file under ./data/output/
4. Reply in-thread with a preview of the cleaned data

Notes

- MVP targets Open Access journals (Nature Comms, PLOS, etc.). Paywalled papers will fail at the scrape step.
- Cleaned files are saved locally, not uploaded to Slack (often too large).
- Logs go to stdout; bump LOG_LEVEL=DEBUG in .env for verbose tracing.
