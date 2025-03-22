from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_AUTH = os.getenv('TWILIO_AUTH')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
NOTIFICATIONS = os.getenv('NOTIFICATIONS')
TWILIO_FROM = os.getenv('TWILIO_FROM')
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH)

def send_whatsapp_message(message, phone_number):
	message = client.messages.create(
		body=message,
		from_=f'whatsapp:{TWILIO_FROM}',
		to=f'whatsapp:{phone_number}'
	)
	print(message.sid)