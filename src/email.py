import requests

EMAIL_TEMPLATE = {
    "round_opened": {"subject": "Round has opened", "text": "Place your bids/offers!"},
    "match_done_has_match": {
        "subject": "You got a match!",
        "text": "Open Acquity to check your matches.",
    },
    "match_done_no_match": {
        "subject": "No match!",
        "text": "Your price might be too high/low! Try again.",
    },
}


class EmailService:
    def __init__(self, config):
        self.config = config

    def send_email(self, bcc_list, template):
        data = EMAIL_TEMPLATE[template]
        return requests.post(
            f"{self.config['MAILGUN_API_BASE_URL']}/messages",
            auth=("api", self.config["MAILGUN_API_KEY"]),
            data={
                "from": "Acquity <noreply@acquity.io>",
                "bcc": bcc_list,
                "subject": data["subject"],
                "text": data["text"],
            },
        )
