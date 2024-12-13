import serial
import time
import asyncio
from datetime import datetime

# SIM800L Configuration
SERIAL_PORT = '/dev/serial0'  # Adjust as needed
BAUD_RATE = 9600  # Baud rate for SIM800L

# A queue to hold SMS messages before sending
message_queue = []

# Set of successfully sent message identifiers
sent_messages = set()

# Time limit (e.g., 11:59 PM) after which unresolved messages will be forfeited
TIME_LIMIT = "23:59"

# Sample message data
messages = [
    ['Your child "Odvina, Jave Lester" has logged and is on time', "+639977529742"],
    ['Your child "Cuarteros, Christopher John" has logged and is on time', "+639979378014"]
]

# Function to send a single SMS
async def send_sms(phone_number, message):
    identifier = f"{phone_number}:{message}"  # Unique identifier
    if identifier in sent_messages:
        print(f"Message already sent: {identifier}")
        return True  # Skip already sent messages

    try:
        # Open the serial connection
        sim800l = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1)

        # Function to send a command and get the response
        def send_command(command, wait_time=2):
            sim800l.write(f'{command}\r'.encode())
            time.sleep(wait_time)
            response = sim800l.read_all().decode().strip()
            return response

        # Initialize the SIM800L module
        if "OK" not in send_command('AT'):
            raise ValueError("Module not responding.")
        if "OK" not in send_command('AT+CMGF=1'):  # Set SMS text mode
            raise ValueError("Failed to set SMS mode.")

        # Send SMS
        if ">" not in send_command(f'AT+CMGS="{phone_number}"'):
            raise ValueError("Failed to set recipient.")

        # Send message body and termination character
        sim800l.write(f'{message}\x1A'.encode())
        time.sleep(5)  # Wait for the SIM800L to process the message

        # Read all responses until the buffer is clear
        response = sim800l.read_all().decode().strip()
        print(f"Module response: {response}")

        # Verify if the message was successfully sent
        if "OK" in response:
            sent_messages.add(identifier)
            print(f"Message successfully sent: {identifier}")
            sim800l.close()
            return True
        else:
            print(f"Failed to send message: {identifier}. Response: {response}")
            sim800l.close()
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False  # If any error occurs, return False

# Function to handle sending messages one by one as soon as they are added
async def send_message_immediately():
    while True:
        if message_queue:
            message_data = message_queue.pop(0)  # Get the first message from the queue
            message, phone_number = message_data
            print(f"Attempting to send to {phone_number}: {message}")
            if not await send_sms(phone_number, message):
                print(f"Retrying to send to {phone_number}...")
                message_queue.append(message_data)  # Re-add to the queue for retry
            else:
                print(f"Message sent to {phone_number}.")

        await asyncio.sleep(1)  # Check the queue periodically

# Function to check if the current time is past the cut-off (e.g., 9 AM)
def is_time_limit_reached():
    current_time = datetime.now().strftime("%H:%M")  # Current time in HH:MM format
    return current_time >= TIME_LIMIT

# Function to continuously accept new entries and add messages to the queue
async def accept_new_entries():
    global messages  # Use the pre-defined messages

    for message_data in messages:
        message_queue.append(message_data)  # Add to the queue
        print(f"Message added to queue: {message_data}")
        await asyncio.sleep(1)

# Main function to run both accepting entries and sending SMS asynchronously
async def main():
    print("Starting to accept new entries...")
    await accept_new_entries()

    # Start sending messages in the background
    asyncio.create_task(send_message_immediately())

    # Periodically check for the time limit
    while not is_time_limit_reached():
        print("Waiting for the time limit...")
        await asyncio.sleep(60)

    print("Time limit reached. Forfeiting unresolved messages.")
    if message_queue:
        print(f"Forfeiting {len(message_queue)} unresolved messages.")
        message_queue.clear()

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
