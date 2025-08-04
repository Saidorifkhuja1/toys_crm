import requests
import logging
import os
from threading import Thread

from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from debts.models import MerchantDebt
from user.models import User
from products.models import ProductBatch, ProductPayments


base_read_only_fields = ["id", "created_at", "updated_at", "created_by", "updated_by"]

logger = logging.getLogger(__name__)

TEXTBEE_API_URL = f"https://api.textbee.dev/api/v1/gateway/devices/{os.getenv('TEXTBEE_DEVICE_ID')}/send-sms"


def _send_sms(recipient: str, message: str):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.getenv("TEXTBEE_API_KEY"),
    }
    payload = {"recipients": [recipient], "message": message}

    try:
        response = requests.post(TEXTBEE_API_URL, json=payload, headers=headers)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"SMS send error: {e}")
        return {"error": str(e)}


def send_sms_async(recipient: str, message: str):
    Thread(target=_send_sms, args=(recipient, message)).start()


# def make_product_payment(
#     product_batch: ProductBatch, request: Request, payment: dict, buy_price: int
# ):
#     paid_amount = 0
#     payment_list = []
#     if payment_iter := payment.get("payments", None):
#         exchange_rate = payment.get("exchange_rate")
#         for payment in payment_iter:
#             payment_list.append(
#                 ProductPayments(
#                     product_batch=product_batch,
#                     created_by=request.user,
#                     **payment,
#                 )
#             )
#             if payment["method"].upper() in ["CARD", "UZS"]:
#                 paid_amount += payment["amount"]
#             elif payment["method"] == "USD":
#                 paid_amount += exchange_rate * payment["amount"]
#             else:
#                 raise ValidationError("Invalid Payment type provided")
#     MerchantDebt.objects.create(
#         amount=buy_price - paid_amount,
#         merchant=request.user,
#         product_batch=product_batch,
#         exchange_rate=exchange_rate,
#     )
#     ProductPayments.objects.bulk_create(payment_list)


def parse_product_payments(payment_data: dict, request_user) -> tuple[list, int, int]:
    """
    Parse payments data and return:
    - list of ProductPayments instances (unsaved)
    - total paid amount in UZS
    - exchange rate
    """
    paid_amount = 0
    payment_list = []
    exchange_rate = payment_data.get("exchange_rate")

    if not exchange_rate:
        raise ValidationError("Exchange rate must be provided.")

    payment_iter = payment_data.get("payments", [])
    for payment in payment_iter:
        payment_list.append(
            ProductPayments(
                created_by=request_user,
                method=payment["method"],
                amount=payment["amount"],
            )
        )
        if payment["method"].lower() in ["card", "uzs"]:
            paid_amount += payment["amount"]
        elif payment["method"].lower() == "usd":
            paid_amount += exchange_rate * payment["amount"]
        else:
            raise ValidationError("Invalid payment type provided.")

    return payment_list, paid_amount, exchange_rate


def make_product_payment(product_batch: ProductBatch, user: User, payment: dict):
    payment_list, paid_amount, exchange_rate = parse_product_payments(payment, user)

    MerchantDebt.objects.create(
        amount=product_batch.buy_price * product_batch.quantity - paid_amount,
        merchant=user,
        product_batch=product_batch,
        exchange_rate=exchange_rate,
    )
    ProductPayments.objects.bulk_create(payment_list)
