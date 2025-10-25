import requests
import base64
from datetime import datetime
from typing import Optional
import json
import os
try:
    from config import CONSUMER_KEY, CONSUMER_SECRET, SHORTCODE, PASSKEY, CALLBACK_URL
except Exception:
    # config may not exist if run standalone; fall back to env
    from dotenv import load_dotenv
    load_dotenv()
    CONSUMER_KEY = os.getenv('CONSUMER_KEY')
    CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
    SHORTCODE = os.getenv('SHORTCODE')
    PASSKEY = os.getenv('PASSKEY')
    CALLBACK_URL = os.getenv('CALLBACK_URL')


def get_access_token(consumer_key: Optional[str] = None, consumer_secret: Optional[str] = None) -> str:
    """Request an OAuth access token from Safaricom sandbox.

    Returns the access token string. Raises on network or parsing errors.
    """
    consumer_key = consumer_key or CONSUMER_KEY
    consumer_secret = consumer_secret or CONSUMER_SECRET
    if not consumer_key or not consumer_secret:
        raise RuntimeError('Missing consumer_key or consumer_secret')

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, auth=(consumer_key, consumer_secret), timeout=10)
    resp.raise_for_status()
    j = resp.json()
    return j.get('access_token')


def generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    data_to_encode = shortcode + passkey + timestamp
    return base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')


def lipa_na_mpesa_online(phone_number: str, amount: int,
                         account_reference: str = 'Payment',
                         transaction_desc: str = 'Payment',
                         consumer_key: Optional[str] = None,
                         consumer_secret: Optional[str] = None,
                         shortcode: Optional[str] = None,
                         passkey: Optional[str] = None,
                         callback_url: Optional[str] = None,
                         merchant_id: Optional[str] = None) -> requests.Response:
    """Initiate an STK Push (Lipa Na M-Pesa Online).

    Returns the requests.Response from the STK endpoint so callers can inspect status/text.
    """
    consumer_key = consumer_key or CONSUMER_KEY
    consumer_secret = consumer_secret or CONSUMER_SECRET
    shortcode = shortcode or SHORTCODE
    passkey = passkey or PASSKEY
    callback_url = callback_url or CALLBACK_URL

    if not all([consumer_key, consumer_secret, shortcode, passkey, callback_url]):
        raise RuntimeError('Missing one or more required credentials (consumer/shortcode/passkey/callback)')

    access_token = get_access_token(consumer_key, consumer_secret)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(shortcode, passkey, timestamp)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': shortcode,
        'PhoneNumber': phone_number,
        'CallBackURL': callback_url,
        'AccountReference': account_reference,
        'TransactionDesc': transaction_desc,
        'Metadata': {
            'merchant_id': merchant_id or shortcode  # Fall back to shortcode if no merchant_id
        }
    }

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    return resp
