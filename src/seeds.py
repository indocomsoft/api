from src.services import SellerService

SellerService().create_account(
    email="a@a.com", password="acquity", check_invitation=False
)
