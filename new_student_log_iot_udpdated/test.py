import tkinter as tk
from PIL import Image, ImageTk
import csv
import requests
import re
import psycopg2
import socket
import os

from multiprocessing import Queue
from datetime import datetime

from services.database_handler import DatabaseHandler
from services.sms_handler import SMSHandler, start_sms_service

student_contact_list = []

class StudentLog:
    def __init__(self, master):
        self.master = master
        self.master.title("Student Log")
        self.master.geometry("1920x1080")
        self.master.overrideredirect(True)
        self.master.minsize(1280, 800)
        self.master.maxsize(1280, 800)
        self.frame = tk.Frame(self.master, bg="white")
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.slideshow_active = False

        # Initialize the database handler
        self.db_handler = DatabaseHandler(
            user="postgres.jdhopbgiuttrhcqpghyc",
            password="bsitcapstone2024",
            host="aws-0-us-east-1.pooler.supabase.com",
            port="6543",
            dbname="postgres"
        )

        # Start the retry process for pending data
        self.start_retry_process()

        # Initialize the message queue for SMS
        self.message_queue = Queue()

        # Create an instance of SMSHandler
        # self.sms_handler = SMSHandler(self.message_queue)

        # Start the SMS service to begin processing messages
        # self.sms_process = start_sms_service(self.message_queue)

        
        # Fetch and assign student contact list
        self.load_student_contacts()

        self.create_first_page()
        self.master.bind('<Control-x>', self.exit_app)

    def load_student_contacts(self):
        """Fetch student contacts from the database and assign to the global list"""
        global student_contact_list
        try:
            student_contact_list = self.db_handler.get_student_contacts()  # Get the contacts as array of tuples
            print(f"Student contacts loaded: {student_contact_list}")
        except Exception as e:
            print(f"Error loading student contacts: {e}")

    def start_retry_process(self):
        """
        Starts the retry process for the database handler.
        """
        try:
            self.retry_process = self.db_handler.start_retry_process()
        except Exception as e:
            print(f"Error starting retry process: {e}")

    def exit_app(self, event=None):
        """
        Cleanly shuts down processes and closes the application.
        """
        try:
            # Stop the retry process for pending data
            if hasattr(self, 'retry_process') and self.retry_process.is_alive():
                self.retry_process.terminate()

            # Stop the SMS service
            if hasattr(self, 'sms_process') and self.sms_process.is_alive():
                self.sms_process.terminate()

        except Exception as e:
            print(f"Error while shutting down: {e}")
        finally:
            self.master.destroy()

 
    def create_first_page(self):
        self.start_idleness_monitor()
 
        # Create the entry widget for user input with validation
        self.entry = tk.Entry(self.frame, width=40, validate="key")
        self.entry['validatecommand'] = (self.entry.register(self.validate_entry), '%d', '%i', '%S', '%P', '%s', '%v', '%V', '%W', '%e')
        self.entry.place(x=11500, y=80)  # Place the entry widget at coordinates (500, 80)
 
        # Bind keypress event to capture information
        self.entry.bind('<Return>', lambda event: self.capture_information(event))
 
        # Focus the entry widget so that the user can immediately start typing
        self.entry.focus_set()
 
        # Load and display an animated GIF image
        self.image_frames = []
        self.load_image_frames("new_student_log_iot_udpdated/resources/qr-code.gif", 0)  # Load frames of the GIF
        self.current_frame = 0
        self.animate_gif()
 
        # bg image
        upper = Image.open("new_student_log_iot_udpdated/resources/upper.png")
        upper =upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=930, y=0)
 
        lower = Image.open("new_student_log_iot_udpdated/resources/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=420)
 
        ustp = Image.open("new_student_log_iot_udpdated/resources/ustp.png")
        ustp = ustp.resize((100, 100))
        photo = ImageTk.PhotoImage(ustp)
        self.upper_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.upper_image_label.image = photo  
        self.upper_image_label.place(x=20, y=10)
 
        dit = Image.open("new_student_log_iot_udpdated/resources/dit.jpg")
        dit = dit.resize((100, 100))
        photo = ImageTk.PhotoImage(dit)
        self.dit_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth= 1)
        self.dit_label.image = photo  
        self.dit_label.place(x=150, y=10)
 
        citc = Image.open("new_student_log_iot_udpdated/resources/citc.jpg")
        citc = citc.resize((200, 100))
        photo = ImageTk.PhotoImage(citc)
        self.citc_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth= 1)
        self.citc_label.image = photo  
        self.citc_label.place(x=1050, y=10)
 
        self.label_top = tk.Label(self.frame, text="Please Present your Student ID to the Scanner", font=("Arial", 24), bg="white")
        self.label_top.place(x=300, y=60)  # Place the label at coordinates (500, 50)
 
    def start_idleness_monitor(self):
        self.idle_counter = 0
        self.frame.bind("<Motion>", self.reset_idleness_counter)
        self.check_idleness()
        print("Monitoring Started")
 
    def reset_idleness_counter(self, event):
        self.idle_counter = 0
 
    def stop_idleness_monitor(self):
        self.frame.unbind("<Motion>")
        self.check_idleness = lambda: None
        print("Monitoring is stopped")
 
    def check_idleness(self):   
        if self.slideshow_active:
            # Slideshow is active, stop idleasness monitoring
            self.idle_counter = 0
        else:
            # Slideshow is not active, continue idleness monitoring
            if self.idle_counter >= 200:  # Assuming 50 iterations equals to 5 seconds
                self.show_slideshow()
                self.idle_counter = 0
            else:
                self.idle_counter += 1
        self.master.after(100, self.check_idleness)
 
    def show_slideshow(self):
        # Create a Toplevel window for the slideshow
        self.slideshow_active = True 
        self.slideshow_window = tk.Toplevel(self.frame)
        self.slideshow_window.overrideredirect(True)  # Remove window decorations
 
        # Bind click event to close the slideshow when clicked
        self.slideshow_window.bind("<Button-1>", lambda event: self.close_slideshow())
 
        # Load images for the slideshow
        self.slideshow_images = []
        for i in range(1, 5):  # Assuming you have images named slide1.jpg, slide2.jpg, slide3.jpg
            image = Image.open(f"new_student_log_iot_udpdated/resources/sample_{i}.png")
            image = image.resize((1280,800))
            photo = ImageTk.PhotoImage(image)
            self.slideshow_images.append(photo)
 
        # Create a label to display the images
        self.slideshow_label = tk.Label(self.slideshow_window, bg="white")
        self.slideshow_label.pack()
 
        # Show the first image
        self.current_slideshow_image = 0
        self.update_slideshow()
 
    def update_slideshow(self):
        self.slideshow_label.config(image=self.slideshow_images[self.current_slideshow_image])
 
        # Display the next image after 3 seconds
        self.current_slideshow_image += 1
        if self.current_slideshow_image >= len(self.slideshow_images):
            self.current_slideshow_image = 0
        self.slideshow_label.after(7000, self.update_slideshow)
 
    def close_slideshow(self):
        if self.slideshow_window:
            self.slideshow_window.destroy()
            self.idle_counter = 0
            self.slideshow_active = False  # Reset slideshow active flag
 
    def validate_entry(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name, event=None):
        if trigger_type in ('key', 'focusout') and action == '1':
            self.capture_information(event)
            return True
        else:
            return False

    def go_to_compare(self, student):
        global student_contact_list

        # Iterate through the student_contact_list (2D list)
        for entry in student_contact_list:
            # Compare the LRN (first element of student) with each entry in student_contact_list
            if str(student).strip() == str(entry[0]).strip():  # Match LRN
                student = [entry[0], entry[1], entry[2]]  # Overwrite student data with the matched contact
                print(f"Match found: Name={entry[1]}, Phone={entry[2]}")
                return student  # Stop after the first match

        # If no match is found
        print("No match found in student_contact_list.")
        return [student, "Unknown Student", ""]  # Return the original student with empty values for name/phone


    def capture_information(self, event):
        try:
            input_text = self.entry.get()
            student = None

            # Use regular expression to find a 10-digit LRN
            match = re.search(r'\d{10}', input_text)
            if match:
                student = match.group(0)

            if student:
                comparison_results = self.go_to_compare(student)
                attendance_time = datetime.now()

                # Directly access the student data from the list
                student_name = comparison_results[1] if len(comparison_results) > 1 else "Unknown Student"
                parent_contactnumber = comparison_results[2] if len(comparison_results) > 2 else ""

                self.create_second_page(student, student_name, parent_contactnumber)    

        except Exception as e:
            print(f"Error: {e}")


    def submit_data(self, result, student_name, parent_contactnumber):
        testing = True
        current_time_str = ""
        current_date_str = ""

        if testing:
            # Predefined times for testing
            current_time_str = "07:30:00"
            current_date_str = "2025-01-08"

            # Convert strings to datetime objects
            current_time = datetime.strptime(current_time_str, "%H:%M:%S").time()
            current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        else:
            # Use the current date and time
            now = datetime.now()
            current_time = now.time()
            current_date = now.date()

        # Determine attendance status
        if 7 <= current_time.hour <= 7 and 30 <= current_time.minute <= 45:
            status = "on-time"
        elif (7 <= current_time.hour <= 11) or (current_time.hour == 7 and current_time.minute > 45):
            status = "late"
        else:
            status = "outside monitored hours"

        sms_message = f"Your child {student_name} has logged in at {current_time.strftime('%H:%M:%S')} and is {status}."

        # Submit data to the database
        self.db_handler.submit_data(result, current_date, current_time)

        # Queue SMS message
        # self.sms_handler.add_message_to_queue(parent_contactnumber, sms_message)


    def create_second_page(self, result, student_name, parent_contactnumber):
        # Clear the frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.stop_idleness_monitor()

        # Background images
        upper = Image.open("new_student_log_iot_udpdated/resources/upper.png")
        upper = upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=930, y=0)

        lower = Image.open("new_student_log_iot_udpdated/resources/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=420)

        # Logos
        ustp = Image.open("new_student_log_iot_udpdated/resources/ustp.png")
        ustp = ustp.resize((100, 100))
        photo = ImageTk.PhotoImage(ustp)
        self.upper_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.upper_image_label.image = photo  
        self.upper_image_label.place(x=20, y=10)

        dit = Image.open("new_student_log_iot_udpdated/resources/dit.jpg")
        dit = dit.resize((100, 100))
        photo = ImageTk.PhotoImage(dit)
        self.dit_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth=1)
        self.dit_label.image = photo  
        self.dit_label.place(x=150, y=10)

        citc = Image.open("new_student_log_iot_udpdated/resources/citc.jpg")
        citc = citc.resize((200, 100))
        photo = ImageTk.PhotoImage(citc)
        self.citc_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth=1)
        self.citc_label.image = photo  
        self.citc_label.place(x=1050, y=10)

        # Get student image based on LRN
        student_image_path = f"new_student_log_iot_udpdated/resources/students/{result}.jpg"  # Assuming the image folder is named 'student_images' and the image is named after the student's LRN.
        if not os.path.exists(student_image_path):  # Check if the student's image exists
            student_image_path = "new_student_log_iot_udpdated/resources/students/default.jpg"  # Use default image if not found

        # Load and resize the image
        student_image = Image.open(student_image_path)
        student_image = student_image.resize((128, 128))  # Resize image as needed
        student_photo = ImageTk.PhotoImage(student_image)

        # Display student image on the left side
        student_image_label = tk.Label(self.frame, image=student_photo, bg="white")
        student_image_label.image = student_photo  # Keep a reference to avoid garbage collection
        student_image_label.place(x=365, y=415)  # Adjust the position as needed

        # Generate time and date from a single `datetime.now()` call
        now = datetime.now().replace(microsecond=0)
        current_time = now.strftime("%I:%M:%S %p")  # Add AM/PM indicator for clarity
        current_date = now.strftime("%B %d, %Y")

        # Default message and status color
        message = "Scan Successful"
        status_color = "#100440"  # Blue

        # Display status message (fixed message)
        status_message = tk.Label(self.frame, text=message, font=("Arial", 32, "bold"), fg=status_color, bg="white", anchor="center")
        status_message.place(relx=0.5, rely=0.4, anchor="center")

        # Display student information (fixed color for student info)
        student_info_message = f"{student_name}\nTime: {current_time}\nDate: {current_date}"
        student_info_label = tk.Label(self.frame, text=student_info_message, font=("Arial", 28, "bold"), fg="#27099c", bg="white", anchor="center")
        student_info_label.place(relx=0.55, rely=0.6, anchor="center")

        # Call to submit the data
        self.submit_data(result, student_name, parent_contactnumber)

        # Schedule return to the first page after 3 seconds
        self.master.after(3000, self.go_to_first_page)


    def load_image_frames(self, filename, index):
        try:
            self.image = Image.open(filename)
            while True:
                self.image.seek(index)  # Go to the specified frame
                self.image_frames.append(ImageTk.PhotoImage(self.image.copy()))
                index += 1
        except EOFError:
            pass
 
    def animate_gif(self):
        self.label_image = tk.Label(self.frame, bg="white")
        self.label_image.place(x=330, y=140)  # Place the label at coordinates (430, 180)
        self.update_image()
 
    def update_image(self):
        self.label_image.config(image=self.image_frames[self.current_frame])
 
    def original_check_idleness(self):   
        if self.slideshow_active:
            # Slideshow is active, stop idleasness monitoring
            self.idle_counter = 0
        else:
            # Slideshow is not active, continue idleness monitoring
            if self.idle_counter >= 200:  # Assuming 50 iterations equals to 5 seconds
                self.show_slideshow()
                self.idle_counter = 0
            else:
                self.idle_counter += 1
        self.master.after(100, self.check_idleness)
 
    def go_to_first_page(self):
        # Destroy current widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        # Recreate the first page
        self.check_idleness = self.original_check_idleness
        self.create_first_page()

def main():
    root = tk.Tk()
    app = StudentLog(root)

    # Start the retry process after initializing the app
    app.start_retry_process()

    root.mainloop()

if __name__ == "__main__":
    main()