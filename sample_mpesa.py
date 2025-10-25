import requests
import base64
from datetime import datetime

# Your credentials
consumer_key = "dPd7aOxNeBAtQH7LigYM6e3GBoOC7p9GdcE8QB4VR3le9NNF"
consumer_secret = "smcfVorYK3iddm9M8b7NJjb04o7TTfCbBva9Ko08rdPlTVpXEYPFmmesk7GJRzHM"
shortcode = "174379"
passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
callback_url = "https://api.nisaclean.com/safaricom/stk-callback"

def get_access_token(consumer_key, consumer_secret):
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    access_token = response.json()['access_token']
    return access_token

def generate_password(shortcode, passkey, timestamp):
    data_to_encode = shortcode + passkey + timestamp
    encoded = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')
    return encoded

def lipa_na_mpesa_online(phone_number, amount, account_reference, transaction_desc):
    access_token = get_access_token(consumer_key, consumer_secret)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(shortcode, passkey, timestamp)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

if __name__ == "__main__":
    phone = "254796247784"  # Replace with phone number in international format
    amt = 10  # Amount to charge
    account_ref = "Alex Supermarket"
    description = "Purchase for electronics"

    response = lipa_na_mpesa_online(phone, amt, account_ref, description)
    print(response)
