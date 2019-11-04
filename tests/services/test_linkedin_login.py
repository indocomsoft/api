from unittest.mock import patch

from src.config import APP_CONFIG
from src.services import LinkedInLogin

linkedin_login = LinkedInLogin(
    config={
        **APP_CONFIG,
        "CLIENT_ID": "some_client_id",
        "CLIENT_SECRET": "some_client_secret",
    }
)


def test_get_auth_url():
    assert (
        linkedin_login.get_auth_url(redirect_uri=["some_redirect_uri"])
        == "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=some_client_id&redirect_uri=some_redirect_uri&scope=r_liteprofile%20r_emailaddress"
    )


def test_authenticate():
    with patch("src.services.requests.post") as post_mock, patch(
        "src.services.requests.get"
    ), patch("src.services.UserService.create_if_not_exists") as user_mock:
        post_mock.return_value.json = lambda: {"access_token": "some_access_token"}

        assert linkedin_login.authenticate(
            code="some_code", redirect_uri="some_redirect_uri", user_type="buyer"
        ) == {"access_token": "some_access_token"}

        post_mock.assert_any_call(
            "https://www.linkedin.com/oauth/v2/accessToken",
            headers={"Content-Type": "x-www-form-urlencoded"},
            params={
                "grant_type": "authorization_code",
                "code": "some_code",
                "redirect_uri": "some_redirect_uri",
                "client_id": "some_client_id",
                "client_secret": "some_client_secret",
            },
        )

        print(user_mock.call_args[1])
        create_kwargs = user_mock.call_args[1]
        assert create_kwargs["is_buy"]
        assert create_kwargs["auth_token"] == "some_access_token"
