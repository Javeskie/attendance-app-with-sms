from sms_handler import SMSHandler, start_sms_service
from queue import Queue

def test_sms():
    # Create a message queue
    message_queue = Queue()

    # Add messages to the queue one by one
    sms_handler = SMSHandler(message_queue)  # Create an instance of SMSHandler

    sms_handler.add_message_to_queue("+639977529742", "Your child 'Odvina, Jave Lester' has logged and is on-time")
    sms_handler.add_message_to_queue("+639979378014", "Your child 'Cuarteros, Christopher John' has logged and is on-time")
    
    # Start the SMS service to begin sending the messages
    start_sms_service(message_queue)

# Run the test
if __name__ == "__main__":
    test_sms()
