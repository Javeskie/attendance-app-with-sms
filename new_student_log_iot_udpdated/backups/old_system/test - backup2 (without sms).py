import tkinter as tk
from PIL import Image, ImageTk
import csv
import requests

from datetime import datetime
import psycopg2
import socket
 
class StudentLog:

    def __init__(self, master):
        self.master = master
        self.master.title("Student Log")
        self.master.geometry("1920x1080")  # Set window size to 1920x1080
        self.master.overrideredirect(True)
        self.master.minsize(1280, 800)
        self.master.maxsize(1280, 800)
        self.frame = tk.Frame(self.master, bg="white")  # Set background color to white
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)  # Place the frame to fill the entire window
        self.slideshow_active = False
        self.create_first_page()
 
        self.master.bind('<Control-x>', self.exit_app)
 
    def exit_app(self, event=None):
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
        self.load_image_frames("/home/group5/Desktop/new_student_log_iot_udpdated/qr-code.gif", 0)  # Load frames of the GIF
        self.current_frame = 0
        self.animate_gif()
 
        # bg image
        upper = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/upper.png")
        upper =upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=930, y=0)
 
        lower = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=420)
 
        ustp = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/ustp.png")
        ustp = ustp.resize((100, 100))
        photo = ImageTk.PhotoImage(ustp)
        self.upper_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.upper_image_label.image = photo  
        self.upper_image_label.place(x=20, y=10)
 
        dit = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/dit.jpg")
        dit = dit.resize((100, 100))
        photo = ImageTk.PhotoImage(dit)
        self.dit_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth= 1)
        self.dit_label.image = photo  
        self.dit_label.place(x=150, y=10)
 
        citc = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/citc.jpg")
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
            image = Image.open(f"sample_{i}.png")
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
 
    def capture_information(self, event):
        try:
            input_text = self.entry.get()
            result = None

            # Extract 10-digit student LRN
            for i in range(len(input_text)):
                if input_text[i].isdigit():
                    if i + 10 <= len(input_text) and input_text[i:i + 10].isdigit():
                        result = input_text[i:i + 10]
                        break

            # Validate student LRN
            if result and len(result) == 10 and result.isdigit():
                # Get the student's name using go_to_compare
                student_name = self.go_to_compare(result)

                # Generate timestamp for attendance
                attendance_time = datetime.now()

                # Submit attendance data with the correct number of arguments
                submission_result = self.submit_data(result, attendance_time)

                # Display results based on the submission
                self.id_label = tk.Label(self.frame, text=f"Student ID = {result}")
                self.id_label.place(x=535, y=200)
                self.id_label.configure(bg='white', fg='#FF0000', font=('Arial', 15))

                # Pass submission_result and student_name to create_second_page
                self.create_second_page(submission_result, student_name)

        except Exception as e:
            print(e)

  
 
    def go_to_compare(self, result):
        csv_files = ['/home/group5/Desktop/new_student_log_iot_udpdated/official_list_it_students.csv']
        student_name = ""  # Initialize student_name as an empty string

        if result == "0000000000":
            student_name = "VISITOR"
        else:
            for csv_file in csv_files:
                with open(csv_file, 'r', encoding="latin-1") as file:
                    csv_reader = csv.reader(file)

                    # Skip header row
                    next(csv_reader, None)

                    for row in csv_reader:
                        # Assuming result is compared with the first column (LRN)
                        if result == row[0]:
                            # Store the student's name from the second column
                            student_name = row[1]
                            print(f"Match found in {csv_file}. Student Name: {row[1]}")
                            return student_name  # Stop searching if a match is found

        print(f"No match found in any CSV file.")
        return student_name

    def check_internet(self):
        try:
            # Attempt to connect to a public DNS server (e.g., Google DNS)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
   

    def submit_data(self, student_lrn, attendance_time):
        if not self.check_internet():
            print("No internet connection. Please check your network and try again.")
            return "no_internet"

        user = "postgres.jdhopbgiuttrhcqpghyc"
        password = "bsitcapstone2024"  # Replace this with your actual password
        host = "aws-0-us-east-1.pooler.supabase.com"
        port = "6543"
        dbname = "postgres"

        try:
            # Establish a connection to the database
            connection = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                dbname=dbname
            )
            cursor = connection.cursor()

            # Call the process_attendance database function
            query = """
                SELECT process_attendance(%s, %s);
            """

            # cursor.execute(query, (student_lrn, attendance_time)) # Real parameters
            cursor.execute(query, (student_lrn, "2024-11-20 07:30:00")) # For default demonstration purposes only
            
            result = cursor.fetchone()[0]  # Fetch the result from the function

            connection.commit()  # Commit the transaction
            print(f"Attendance submission result: {result}")
            return result

        except psycopg2.OperationalError as e:
            print(f"Operational error: {e}")
            return "db_error"

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "error"

        finally:
            if 'connection' in locals() and connection:
                cursor.close()
                connection.close()
                print("Database connection closed.")

 
    def create_second_page(self, submission_result, student_name):
        # Clear the frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.stop_idleness_monitor()

        # bg image
        upper = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/upper.png")
        upper = upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=900, y=0)

        lower = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=350)

        ustp = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/ustp.png")
        ustp = ustp.resize((100, 100))
        photo = ImageTk.PhotoImage(ustp)
        self.upper_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.upper_image_label.image = photo  
        self.upper_image_label.place(x=20, y=10)

        dit = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/dit.jpg")
        dit = dit.resize((100, 100))
        photo = ImageTk.PhotoImage(dit)
        self.dit_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth=1)
        self.dit_label.image = photo  
        self.dit_label.place(x=150, y=10)

        citc = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/citc.jpg")
        citc = citc.resize((200, 100))
        photo = ImageTk.PhotoImage(citc)
        self.citc_label = tk.Label(self.frame, image=photo, bg="blue", borderwidth=1)
        self.citc_label.image = photo  
        self.citc_label.place(x=1050, y=10)

        # Generate time of attendance
        current_time = datetime.now().strftime("%I:%M:%S %p")  # Time in 12-hour format
        current_date = datetime.now().strftime("%B %d, %Y")    # Date with full month name

        # Determine the status and set message and color
        if submission_result == "no_internet":
            message = "Attendance Failed - No internet"
            status_color = "#870808"  # Darker red
        elif submission_result == "exist":
            message = "Attendance Already Existed"
            status_color = "#fc5e03"  # Darker yellow
        elif submission_result == "success":
            message = "Attendance Successful"
            status_color = "#100440"  # Blue
        elif submission_result == "timeout":
            message = "Attendance Too Early"
            status_color = "#750c87"  # Darker orange
        else:
            message = "Attendance Failed - Unknown Error"
            status_color = "#6C757D"  # Dark gray

        # Display status message (status color is applied only to the message)
        status_message = tk.Label(self.frame, text=message, font=("Arial", 32, "bold"), fg=status_color, bg="white", anchor="center")
        status_message.place(relx=0.5, rely=0.4, anchor="center")

        # Display student information (fixed color for studesnt info)
        student_info_message = f"{student_name}\nTime: {current_time}\nDate: {current_date}"
        student_info_label = tk.Label(self.frame, text=student_info_message, font=("Arial", 28, "bold"), fg="#27099c", bg="white", anchor="center")
        student_info_label.place(relx=0.5, rely=0.6, anchor="center")

        # Schedule return to the first page after 5 seconds
        self.master.after(5000, self.go_to_first_page)
   
    def go_to_last(self, student_name, attendance_time):
        for widget in self.frame.winfo_children():
            widget.destroy()

        # bg image
        upper = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/upper.png")
        upper = upper.resize((400, 300))
        photo = ImageTk.PhotoImage(upper)
        self.static_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.static_image_label.image = photo  
        self.static_image_label.place(x=930, y=0)

        lower = Image.open("/home/group5/Desktop/new_student_log_iot_udpdated/lower.png")
        lower = lower.resize((400, 300))
        photo = ImageTk.PhotoImage(lower)
        self.lower_image_label = tk.Label(self.frame, image=photo, bg="white")
        self.lower_image_label.image = photo
        self.lower_image_label.place(x=0, y=420)

        # Display student name and attendance time
        student_info = f"Student: {student_name}\nTime: {attendance_time}"
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
 
if __name__ == "__main__":
    root = tk.Tk()
    app = StudentLog(root)
    root.mainloop()
 
