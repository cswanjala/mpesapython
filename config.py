from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from project root if exists
ROOT = Path(__file__).parent
env_path = ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # fall back to default behavior (searches current environment)
    load_dotenv()

# Centralized config values
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
SHORTCODE = os.getenv('SHORTCODE')
PASSKEY = os.getenv('PASSKEY')
CALLBACK_URL = os.getenv('CALLBACK_URL')
C2B_CALLBACK_URL = os.getenv('C2B_CALLBACK_URL')
SERVER_URL = os.getenv('SERVER_URL')
LOGIN_URL = os.getenv('LOGIN_URL')
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL')

# Helper to get raw env if needed
def get(key, default=None):
    return os.getenv(key, default)
