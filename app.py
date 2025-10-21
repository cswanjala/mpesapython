from flask import Flask, request, jsonify
from plyer import notification
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

def show_notification(title, message):
    """Display a desktop notification"""
    notification.notify(
        title=title,
        message=message,
        app_icon=None,  # e.g. 'C:\\icon_32x32.ico'
        timeout=10,  # seconds
    )

@app.route('/stk-callback', methods=['POST'])
def stk_callback():
    """Handle STK push callbacks"""
    data = request.get_json()
    
    # Extract relevant information from callback
    try:
        body = data.get('Body', {})
        result = body.get('stkCallback', {})
        result_code = result.get('ResultCode')
        
        if result_code == 0:  # Successful transaction
            metadata = result.get('CallbackMetadata', {}).get('Item', [])
            amount = next((item['Value'] for item in metadata if item['Name'] == 'Amount'), 0)
            phone = next((item['Value'] for item in metadata if item['Name'] == 'PhoneNumber'), '')
            transaction_id = next((item['Value'] for item in metadata if item['Name'] == 'MpesaReceiptNumber'), '')
            
            message = f"Amount: KES {amount}\\nFrom: {phone}\\nTransaction ID: {transaction_id}"
            show_notification("M-Pesa Payment Received!", message)
        else:
            result_desc = result.get('ResultDesc', 'Transaction failed')
            show_notification("M-Pesa Payment Failed", result_desc)
            
    except Exception as e:
        show_notification("Error Processing Payment", str(e))
    
    return jsonify({"status": "success"}), 200

@app.route('/c2b-callback', methods=['POST'])
def c2b_callback():
    """Handle direct till (C2B) payment callbacks"""
    data = request.get_json()
    
    try:
        transaction_type = data.get('TransactionType', '')
        amount = data.get('TransAmount', '')
        transaction_id = data.get('TransID', '')
        phone = data.get('MSISDN', '')  # Customer's phone number
        
        message = (
            f"Transaction Type: {transaction_type}\\n"
            f"Amount: KES {amount}\\n"
            f"From: {phone}\\n"
            f"Transaction ID: {transaction_id}"
        )
        show_notification("Till Payment Received!", message)
        
    except Exception as e:
        show_notification("Error Processing Till Payment", str(e))
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    
    # Notify that the server is starting
    show_notification(
        "M-Pesa Callback Server",
        f"Server is running on port {port}\\nReady to receive callbacks!"
    )
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)