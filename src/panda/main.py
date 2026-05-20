import logging

from panda.config import Settings
from panda.slack.app import create_app


def main():
    settings = Settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    app = create_app(settings)

    from slack_bolt.adapter.socket_mode import SocketModeHandler

    handler = SocketModeHandler(app, settings.slack_app_token)
    logging.getLogger(__name__).info("Starting Panda Data Agent in Socket Mode...")
    handler.start()


if __name__ == "__main__":
    main()
