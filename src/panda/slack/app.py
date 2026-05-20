from slack_bolt import App

from panda.config import Settings
from panda.slack.listeners import register_listeners


def create_app(settings: Settings) -> App:
    app = App(
        token=settings.slack_bot_token,
        signing_secret=settings.slack_signing_secret,
    )
    register_listeners(app, settings)
    return app
