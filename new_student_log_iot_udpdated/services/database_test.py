from datetime import datetime
from database_handler import DatabaseHandler

# Define a test function to verify the database_handler functionality
def test_database_handler():
    # Initialize the DatabaseHandler with production credentials
    db_handler = DatabaseHandler(
        user="postgres.jdhopbgiuttrhcqpghyc", 
        password="bsitcapstone2024", 
        host="aws-0-us-east-1.pooler.supabase.com", 
        port="6543", 
        dbname="postgres"
    )

    # Define test values
    test_student_lrn = "2021301287"
    test_attendance_time = datetime.strptime("2024-11-19 07:46:00", "%Y-%m-%d %H:%M:%S")

    print("Testing database submission with test values...")

    # Submit data and print the result
    submit_result = db_handler.submit_data(test_student_lrn, test_attendance_time)
    print(f"Submit Result: {submit_result}")

    # Simulate retrying pending data
    print("Simulating retrying pending data...")
    db_handler.retry_pending_data()

# Run the test
if __name__ == "__main__":
    test_database_handler()
