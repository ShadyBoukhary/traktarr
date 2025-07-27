import requests

from misc.log import logger

log = logger.get_logger(__name__)


class Discord:
    NAME = "Discord"

    def __init__(self, webhook_url, username='Traktarr', avatar_url=None):
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url
        log.debug("Initialized Discord notification agent")

    def send(self, **kwargs):
        if not self.webhook_url or not self.username:
            log.error("You must specify a webhook_url and username when initializing this class")
            return False

        # send notification
        try:
            payload = {
                'content': kwargs['message'],
                'username': self.username,
            }
            
            # Add avatar URL if provided
            if self.avatar_url:
                payload['avatar_url'] = self.avatar_url

            resp = requests.post(self.webhook_url, json=payload, timeout=30)
            return resp.status_code == 204  # Discord returns 204 for successful webhook

        except Exception:
            log.exception("Error sending notification to %r", self.webhook_url)
        return False
