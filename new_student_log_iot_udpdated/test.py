import tkinter as tk
from PIL import Image, ImageTk
import csv
import requests
import re
import psycopg2
import socket

from multiprocessing import Queue
from datetime import datetime

from services.database_handler import DatabaseHandler
from services.sms_handler import SMSHandler, start_sms_service


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

        # Initialize the message queue for SMS
        self.message_queue = Queue()

        # Create an instance of SMSHandler
        self.sms_handler = SMSHandler(self.message_queue)

        # Start the SMS service to begin processing messages
        self.sms_process = start_sms_service(self.message_queue)

        self.create_first_page()
        self.master.bind('<Control-x>', self.exit_app)

    def start_retry_process(self):
        # Start the retry process for pending data
        self.retry_process = self.db_handler.start_retry_process()

    def exit_app(self, event=None):
        # Make sure to stop the retry process and SMS service when exiting
        if hasattr(self, 'retry_process') and self.retry_process.is_alive():
            self.retry_process.terminate()
        if hasattr(self, 'sms_process') and self.sms_process.is_alive():
            self.sms_process.terminate()
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
        self.load_image_frames("/resources/qr-code.gif", 0)  # Load frames of the GIF
        self.current_frame = 0
        self.animate_gif()
 
        # bg image
        upper = Image.open("/resources/upper.png")
        upper =upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=930, y=0)
 
        lower = Image.open("/resources/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=420)
 
        ustp = Image.open("/resources/ustp.png")
        ustp = ustp.resize((100, 100))
        photo = ImageTk.PhotoImage(ustp)
        self.upper_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.upper_image_label.image = photo  
        self.upper_image_label.place(x=20, y=10)
 
        dit = Image.open("/resources/dit.jpg")
        dit = dit.resize((100, 100))
        photo = ImageTk.PhotoImage(dit)
        self.dit_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth= 1)
        self.dit_label.image = photo  
        self.dit_label.place(x=150, y=10)
 
        citc = Image.open("/resources/citc.jpg")
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
            image = Image.open(f"/resources/sample_{i}.png")
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

    def go_to_compare(self, result):
        csv_files = ['/resources/official_list_it_students.csv']
        comparison_results = {"name": "", "phone": ""}

        for csv_file in csv_files:
            try:
                with open(csv_file, 'r', encoding="latin-1") as file:
                    csv_reader = csv.reader(file)
                    next(csv_reader, None)  # Skip header row

                    for row in csv_reader:
                        if len(row) >= 3 and result == row[0]:  # Ensure there are at least 3 columns
                            comparison_results["name"] = row[1]  # Name
                            comparison_results["phone"] = row[2]  # Phone number
                            print(f"Match found: Name={row[1]}, Phone={row[2]}")
                            return comparison_results  # Stop after the first match
            except FileNotFoundError:
                print(f"File not found: {csv_file}")
                return comparison_results  # Return empty if file not found

        print("No match found in CSV.")
        return comparison_results



    def capture_information(self, event):
        try:
            input_text = self.entry.get()
            result = None

            # Use regular expression to find a 10-digit LRN
            match = re.search(r'\d{10}', input_text)
            if match:
                result = match.group(0)

            if result:
                comparison_results = self.go_to_compare(result)
                attendance_time = datetime.now()

                # Extract student name and phone number
                student_name = comparison_results.get("name", "Unknown Student")
                parent_contactnumber = comparison_results.get("phone", "")

                self.submit_data(result, student_name, parent_contactnumber)

                self.create_second_page(result, student_name)    

        except Exception as e:
            print(f"Error: {e}")


    def submit_data(self, student_lrn, student_name, parent_contactnumber):
        testing=True

        attendance_time = ""
        current_time = "" 

        # If testing is True, use predefined times
        if testing:
            attendance_time_str = "2024-12-16 07:44:00"
            current_time_str = "2024-12-16 07:45:00"
            # Convert the strings to datetime objects
            attendance_time = datetime.strptime(attendance_time_str, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.strptime(current_time_str, "%Y-%m-%d %H:%M:%S")

        else:
            # Normal logic
            attendance_time = datetime.now()
            current_time = attendance_time.strftime("%I:%M %p")

        # Determine attendance status
        if 7 <= attendance_time.hour <= 7 and 30 <= attendance_time.minute <= 45:
            status = "on-time"
        elif (7 <= attendance_time.hour <= 11) or (attendance_time.hour == 7 and attendance_time.minute > 45):
            status = "late"
        else:
            status = "outside monitored hours"

        sms_message = f"Your child {student_name} has logged in at {current_time} and is {status}."

        # Use the new DatabaseHandler class to handle data submission
        self.db_handler.submit_data(student_lrn, attendance_time)

        # Call the add_message_to_queue method via the sms_handler instance
        # self.sms_handler.add_message_to_queue(parent_contactnumber, sms_message)

    def create_second_page(self, submission_result, student_name):
        # Clear the frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.stop_idleness_monitor()

        # bg image
        upper = Image.open("/resources/upper.png")
        upper = upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=900, y=0)

        lower = Image.open("/resources/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=350)

        ustp = Image.open("/resources/ustp.png")
        ustp = ustp.resize((100, 100))
        photo = ImageTk.PhotoImage(ustp)
        self.upper_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.upper_image_label.image = photo  
        self.upper_image_label.place(x=20, y=10)

        dit = Image.open("/resources/dit.jpg")
        dit = dit.resize((100, 100))
        photo = ImageTk.PhotoImage(dit)
        self.dit_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth=1)
        self.dit_label.image = photo  
        self.dit_label.place(x=150, y=10)

        citc = Image.open("/resources/citc.jpg")
        citc = citc.resize((200, 100))
        photo = ImageTk.PhotoImage(citc)
        self.citc_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth=1)
        self.citc_label.image = photo  
        self.citc_label.place(x=1050, y=10)

        # Generate time of attendance
        current_time = datetime.now().replace(microsecond=0).strftime("%I:%M:%S")
        current_date = datetime.now().replace(microsecond=0).strftime("%B %d, %Y")

        # Default message and status color (regardless of the submission result)
        message = "Scan Successful"
        status_color = "#100440"  # Blue

        # Display status message (fixed message)
        status_message = tk.Label(self.frame, text=message, font=("Arial", 32, "bold"), fg=status_color, bg="white", anchor="center")
        status_message.place(relx=0.5, rely=0.4, anchor="center")

        # Display student information (fixed color for student info)
        student_info_message = f"{student_name}\nTime: {current_time}\nDate: {current_date}"
        student_info_label = tk.Label(self.frame, text=student_info_message, font=("Arial", 28, "bold"), fg="#27099c", bg="white", anchor="center")
        student_info_label.place(relx=0.5, rely=0.6, anchor="center")

        # Schedule return to the first page after 5 seconds
        self.master.after(3000, self.go_to_first_page)

   
    def go_to_last(self, student_name, attendance_time):
        for widget in self.frame.winfo_children():
            widget.destroy()

        # bg image
        upper = Image.open("/resources/upper.png")
        upper = upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=930, y=0)

        lower = Image.open("/resources/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=420)

        # Display student name and attendance time
        student_info = f"/resources/Student: {student_name}\nTime: {attendance_time}"
        student_info_label = tk.Label(self.frame, text=student_info, font=("Arial", 24, "bold"), fg="black", bg="white")
        student_info_label.place(relx=0.5, rely=0.5, anchor="center")

        # Schedule return to first page after 3 seconds
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