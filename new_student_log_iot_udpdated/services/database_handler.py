import psycopg2
import socket
from datetime import datetime
from collections import deque
from contextlib import contextmanager
from multiprocessing import Process, Queue, Lock
import time


class DatabaseHandler:
    def __init__(self, user, password, host, port, dbname):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        self.pending_data_queue = deque()  # Queue to store pending data until internet is available
        self.message_queue = Queue()  # Queue to handle the messaging process
        self.serial_lock = Lock()  # Lock for serial communication

    # Check if internet connection is available
    def check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    # Database connection management using context manager
    @contextmanager
    def get_connection(self):
        connection = psycopg2.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            dbname=self.dbname
        )
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            connection.commit()
            cursor.close()
            connection.close()

    # Function to fetch student contacts and return them as a 2D array
    def get_student_contacts(self):
        try:
            query = "SELECT student_lrn, student_name, parent_phone FROM student_contacts;"
            with self.get_connection() as cursor:
                cursor.execute(query)
                contacts = cursor.fetchall()  # This returns an array of tuples
                print("Student Contacts Retrieved:")

                # Convert the list of tuples to a 2D array
                student_contacts = []
                for contact in contacts:
                    # Split the name and ensure the correct format for the middle name
                    student_lrn = contact[0]
                    student_name = contact[1]
                    phone_number = contact[2]           
                
                    student_contacts.append([student_lrn, student_name, phone_number])
                
                    print([student_lrn, student_name, phone_number])  # Print the formatted contact

                print(f"Student contacts loaded: {student_contacts}")
                return student_contacts  # Return the 2D list of student contacts
        except psycopg2.Error as e:
            print(f"Database Error: {e}")
            return []  # Return an empty list if there's a database error
        except Exception as e:
            print(f"Unexpected error fetching student contacts: {e}")
            return []  # Return an empty list in case of unexpected errors

    # Commit data to the database
    def commit_data_to_db(self, student_lrn, monitoring_date, monitoring_time):
        try:
            # print(f"Print Test: {student_lrn} + {monitoring_date} + {monitoring_time}")
        
            # Explicitly cast monitoring_date to DATE and monitoring_time to TIME in the query
            query = "SELECT process_monitoring(%s, %s::DATE, %s::TIME);"
        
            with self.get_connection() as cursor:
                cursor.execute(query, (student_lrn, monitoring_date, monitoring_time))
                result = cursor.fetchone()[0]
                print(f"Attendance submission result: {result}")
                return result
        except psycopg2.Error as e:
            print(f"Database Error: {e}")
            return "error"
        except Exception as e:
            print(f"Unexpected error committing data: {e}")
            return "error"



    # Submit data (either immediate or from queue if no internet)
    def submit_data(self, student_lrn, monitoring_date, monitoring_time):
        if not self.check_internet():
            print("No internet connection. Queuing data.")
            self.pending_data_queue.append((student_lrn, monitoring_date, monitoring_time))
            return "queued"

        result = self.commit_data_to_db(student_lrn, monitoring_date, monitoring_time)
        return result

    # Function to retry pending data submissions
    def retry_pending_data(self):
        while True:
            if self.check_internet():
                print("Internet available, retrying pending data...")
                while self.pending_data_queue:
                    student_lrn, monitoring_date, monitoring_time = self.pending_data_queue.popleft()
                    print(f"Retrying submission for {student_lrn}, {monitoring_date}, {monitoring_time}")
                    self.commit_data_to_db(student_lrn, monitoring_date, monitoring_time)
            else:
                print("No internet connection. Waiting to retry...")
            time.sleep(5)

    # Function to handle pending data in a separate process
    def start_retry_process(self):
        retry_process = Process(target=self.retry_pending_data)
        retry_process.start()
        return retry_process


# Main function to simulate the process
def main():
    from datetime import datetime

    # Example of initializing the database handler
    db_handler = DatabaseHandler(
        user="postgres.jdhopbgiuttrhcqpghyc",
        password="bsitcapstone2024",
        host="aws-0-us-east-1.pooler.supabase.com",
        port="6543",
        dbname="postgres"
    )

    # Start the retry process
    retry_process = db_handler.start_retry_process()

    # Graceful shutdown
    try:
        retry_process.join()
    except KeyboardInterrupt:
        retry_process.terminate()
        print("Retry process terminated.")


# Ensure the script runs properly on Windows
if __name__ == "__main__":
    main()
