import json

import requests

EMAIL_TEMPLATE = {
    "register_buyer": {
        "subject": "Welcome to Acquity!",
        "text": "Welcome to Acquity! Please wait while our committee approves your request to be a buyer.",
    },
    "register_seller": {
        "subject": "Welcome to Acquity!",
        "text": "Welcome to Acquity! Please wait while our committee approves your request to be a seller.",
    },
    "approved_buyer": {
        "subject": "Your account has been approved",
        "text": "Congratulations, your account has been approved by the committee! You can now put bid requests.",
    },
    "approved_seller": {
        "subject": "Your account has been approved",
        "text": "Congratulations, your account has been approved by the committee! You can now put ask requests.",
    },
    "rejected_buyer": {
        "subject": "Sorry, your account has been rejected",
        "text": "Sorry, your account is not approved by the committee. Please contact the committee if you wish to dispute this.",
    },
    "rejected_seller": {
        "subject": "Sorry, your account has been rejected",
        "text": "Sorry, your account is not approved by the committee. Please contact the committee if you wish to dispute this.",
    },
    "round_opened": {"subject": "Round has opened", "text": "Place your bids/offers!"},
    "create_buy_order": {
        "subject": "Your bid has been created",
        "text": "Your bid has been created! Please wait until the round ends.",
    },
    "create_sell_order": {
        "subject": "Your ask has been created",
        "text": "Your ask has been created! Please wait until the round ends.",
    },
    "edit_buy_order": {
        "subject": "Your bid has been edited",
        "text": "Your bid has been edited! Please wait until the round ends.",
    },
    "edit_sell_order": {
        "subject": "Your ask has been edited",
        "text": "Your ask has been edited! Please wait until the round ends.",
    },
    "match_done_has_match": {
        "subject": "You got a match!",
        "text": "Open Acquity to check your matches.",
    },
    "match_done_no_match": {
        "subject": "No match!",
        "text": "Your price might be too high/low! Try again.",
    },
    "new_user_review": {
        "subject": "A new user has registered",
        "text": "A new user has registered. Please approve/reject him/her.",
    },
}


class EmailService:
    def __init__(self, config):
        self.config = config

    def send_email(self, emails, template):
        if not config["MAILGUN_ENABLE"]:
            return

        data = EMAIL_TEMPLATE[template]
        return requests.post(
            f"{self.config['MAILGUN_API_BASE_URL']}/messages",
            auth=("api", self.config["MAILGUN_API_KEY"]),
            data={
                "from": "Acquity <noreply@acquity.io>",
                "to": emails,
                "recipient-variables": json.dumps({email: {} for email in emails}),
                "subject": data["subject"],
                "text": data["text"],
            },
        )
