"""
Register C2B URLs with Safaricom M-Pesa
"""
from mpesa_client import c2b_register_url
from flask import jsonify
import os
from dotenv import load_dotenv

load_dotenv()

def register_c2b_urls(confirmation_url, validation_url):
    """Register C2B URLs with Safaricom"""
    try:
        result = c2b_register_url(
            shortcode=os.getenv('SHORTCODE'),
            response_type='Completed',
            confirmation_url=confirmation_url,
            validation_url=validation_url,
            consumer_key=os.getenv('CONSUMER_KEY'),
            consumer_secret=os.getenv('CONSUMER_SECRET')
        )
        return result
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    # Example usage
    confirmation = 'https://3b4d22b8307c.ngrok-free.app/c2b-callback'  # Update with your URL
    validation = 'https://3b4d22b8307c.ngrok-free.app/c2b-validation'  # Update with your URL
    result = register_c2b_urls(confirmation, validation)
    print(result)