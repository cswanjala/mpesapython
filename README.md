# M-Pesa Callback Notification Server

This Python application receives M-Pesa callbacks (both STK Push and direct till payments) and displays desktop notifications with the payment details.

## Features

- Receives STK Push callbacks
- Receives C2B (Till) payment callbacks
- Shows desktop notifications for successful payments
- Shows error notifications for failed payments

## Requirements

- Python 3.x
- Flask
- plyer (for desktop notifications)
- python-dotenv
- ngrok or similar tool for exposing local server to the internet

## Setup

1. Install the required packages:
   ```bash
   pip install flask requests plyer python-dotenv
   ```

2. Configure your environment variables in the `.env` file:
   ```
   CONSUMER_KEY=your_consumer_key
   CONSUMER_SECRET=your_consumer_secret
   SHORTCODE=your_shortcode
   PASSKEY=your_passkey
   CALLBACK_URL=your_callback_url
   ```

3. Start ngrok to expose your local server:
   ```bash
   ngrok http 5000
   ```

4. Update your callback URLs in the M-Pesa developer portal with your ngrok URL:
   - STK Push callback: `https://your-ngrok-url/stk-callback`
   - C2B callback: `https://your-ngrok-url/c2b-callback`

5. Run the callback server:
   ```bash
   python app.py
   ```

6. Run the GUI application (in a separate terminal):
   ```bash
   python gui.py
   ```

## Usage

Once both applications are running:
1. The server will show a notification that it has started
2. Listen for callbacks on port 5000
3. Display desktop notifications whenever payments are received
4. Use the GUI to send STK push requests:
   - Enter the phone number (format: 254XXXXXXXXX)
   - Enter the amount in KES
   - Click "Send STK Push"
5. View transaction history in the GUI
6. Handle both successful and failed transactions

## Endpoints

- `/stk-callback` - Receives STK Push callbacks
- `/c2b-callback` - Receives C2B (Till) payment callbacks

## Notes

- Make sure your computer's notification settings allow applications to show notifications
- Keep the application running to receive callbacks
- For production use, consider using a proper web server like Gunicorn