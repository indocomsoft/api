from src.services import SellerService

SellerService().create_account(
    email="a@a.com", password="acquity", full_name="Ben", check_invitation=False
)
