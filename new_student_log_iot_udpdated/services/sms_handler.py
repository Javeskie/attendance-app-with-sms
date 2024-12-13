import serial
import time
from datetime import datetime
from multiprocessing import Process, Queue, Lock

# Configuration constants
SERIAL_PORT = '/dev/serial0'  # Adjust as needed
BAUD_RATE = 9600
TIME_LIMIT = "23:59"

# A set to track successfully sent messages (shared within the process, not across)
sent_messages = set()

class SMSHandler:
    def __init__(self, message_queue, db_handler=None):
        """
        Initializes the SMSHandler with the message queue and optional database handler.
        :param message_queue: Queue for SMS messages to be sent.
        :param db_handler: Optional DatabaseHandler instance for interacting with the DB.
        """
        self.message_queue = message_queue  # Queue for SMS messages
        # self.db_handler = db_handler  # Database handler instance (optional)

    def send_sms(self, phone_number, message, serial_lock):
        """
        Sends a single SMS message to the provided phone number.
        :param phone_number: The phone number to send the SMS to.
        :param message: The message content to send.
        :param serial_lock: Lock to manage concurrent access to the serial port.
        :return: True if SMS was sent successfully, False otherwise.
        """
        identifier = f"{phone_number}:{message}"

        # Skip if the message is already marked as sent
        if identifier in sent_messages:
            return True

        try:
            # Lock the serial port to prevent concurrent access
            with serial_lock:
                # Open the serial connection
                sim800l = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(5)  # Allow time for initialization

                def send_command(command, wait_time=2):
                    """Helper function to send a command and read the response."""
                    sim800l.write(f'{command}\r'.encode())
                    time.sleep(wait_time)
                    return sim800l.read_all().decode().strip()

                # Initialize the SIM800L module
                if "OK" not in send_command('AT'):
                    raise ValueError("Module not responding.")
                if "OK" not in send_command('AT+CMGF=1'):  # Set SMS text mode
                    raise ValueError("Failed to set SMS mode.")

                # Set the recipient
                if ">" not in send_command(f'AT+CMGS="{phone_number}"'):
                    raise ValueError("Failed to set recipient.")

                # Send message body and termination character
                sim800l.write(f'{message}\x1A'.encode())
                time.sleep(5)  # Allow time for the SIM800L to process the message

                # Check if the message was successfully sent
                response = sim800l.read_all().decode().strip()
                if "OK" in response:
                    sent_messages.add(identifier)
                    sim800l.close()
                    return True
                else:
                    sim800l.close()
                    return False

        except Exception as e:
            print(f"Error: {e}")
            return False

    def process_pending_messages(self, serial_lock):
        """
        Fetches pending messages from the queue, sends them, and updates their status.
        Optionally interacts with the database to mark messages as sent.
        """
        while True:
            current_time = datetime.now().strftime("%H:%M")
            if current_time >= TIME_LIMIT:
                print("Time limit reached. Stopping SMS service.")
                break

            if not self.message_queue.empty():
                phone_number, message = self.message_queue.get()  # Get message from the queue
                if not self.send_sms(phone_number, message, serial_lock):
                    print(f"Failed to send to {phone_number}. Retrying...")
                    self.message_queue.put((phone_number, message))  # Re-add for retry
                else:
                    print(f"Message sent to {phone_number}.")

                    # If you have a database handler, mark the message as sent in the DB
                    if self.db_handler:
                        self.db_handler.mark_message_as_done(phone_number, message)

            else:
                time.sleep(1)  # No messages to process; sleep briefly

    def add_message_to_queue(self, phone_number, message):
        """
        Adds a message to the queue to be sent.
        :param phone_number: The phone number to send the message to.
        :param message: The message content.
        """
        self.message_queue.put((phone_number, message))
        print(f"Message added to queue: {phone_number}, {message}")

def start_sms_service(message_queue, db_handler=None):
    serial_lock = Lock()  # Multiprocessing lock for serial access
    sms_handler = SMSHandler(message_queue, db_handler)
    sms_process = Process(target=sms_handler.process_pending_messages, args=(serial_lock,))
    sms_process.start()
    return sms_process
