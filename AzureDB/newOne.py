import sys
import socket
import cv2
import dlib
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit
from PyQt5.QtGui import QPalette, QBrush, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QTimer
from sqlalchemy import create_engine, Table, MetaData, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from picamera2 import Picamera2, Preview
from time import sleep
import pigpio
import os

# Import pigpio for servo control
import pigpio
import os
from time import sleep

os.system("sudo pigpiod")
sleep(1)

pi = pigpio.pi()
if not pi.connected:
    print("not connected")
    exit()

SERVO_PIN = 18

def set_servo_pulsewidth(pulsewidth):
    pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)

# Paths to the model files
predictor_path = 'shape_predictor_68_face_landmarks.dat'
face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'

# Initialize the face detector, shape predictor, and face recognition model
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)
face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)

# Database credentials
server = 'facesystemlock.database.windows.net'
database = 'facesystemlock'
username = 'superadmin'
password = 'LKWW8mLOO&qzV0La4NqYzsGmF'

# Connection string
connection_string = f'mssql+pymssql://{username}:{password}@{server}:1433/{database}'

# Create SQLAlchemy engine
engine = create_engine(connection_string)

# Define metadata
metadata = MetaData()

# Reflect the employee and room tables
employee_table = Table('EMPLOYEE', metadata, autoload_with=engine)
room_table = Table('ROOM', metadata, autoload_with=engine)
log_table = Table('LOG', metadata, autoload_with=engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Room Registration")
        self.setGeometry(100, 100, 800, 480)

        # Create a gradient background
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255))
        gradient.setColorAt(1, QColor(200, 200, 200))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        # Create UI components
        self.name_label = QLabel("Enter Your Name:")
        self.name_input = QLineEdit()
        self.register_button = QPushButton("Register")
        self.recognition_button = QPushButton("Recognize Face")
        self.recognition_label = QLabel("")

        # Connect buttons to functions
        self.register_button.clicked.connect(self.register_face)
        self.recognition_button.clicked.connect(self.recognize_face)

        # Create a layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.register_button)
        layout.addWidget(self.recognition_button)
        layout.addWidget(self.recognition_label)
        self.setLayout(layout)

        # Initialize camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_preview_configuration(main={"format": "RGB888"}))
        self.camera.start_preview(Preview.QTGL)
        self.camera.start()

        # Load known faces and their descriptors
        self.load_known_faces()

        # Get the IP address of the device
        self.ip_address = get_ip_address()

    def load_known_faces(self):
        self.known_face_descriptors = []
        self.known_names = []
        self.known_employee_ids = []

        # Load known faces and their descriptors from the database
        employees = session.query(employee_table).all()
        for employee in employees:
            self.known_names.append(employee.name)
            self.known_employee_ids.append(employee.id)
            descriptor = np.frombuffer(employee.face_descriptor, dtype=np.float64)
            self.known_face_descriptors.append(descriptor)

    def register_face(self):
        name = self.name_input.text().strip()
        if not name:
            self.recognition_label.setText("Please enter a name.")
            return

        # Capture an image from the camera
        frame = self.camera.capture_array()

        # Detect faces in the image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) == 0:
            self.recognition_label.setText("No face detected.")
            return

        face = faces[0]  # Process the first detected face
        landmarks = predictor(gray, face)
        face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)
        np_face_descriptor = np.array(face_descriptor)

        # Store the new face descriptor and name in the database
        new_employee = employee_table.insert().values(
            name=name,
            face_descriptor=np_face_descriptor.tobytes()
        )
        session.execute(new_employee)
        session.commit()

        self.recognition_label.setText(f"Registered {name}")

        # Update the known faces and their descriptors
        self.load_known_faces()

    def recognize_face(self):
        # Capture an image from the camera
        frame = self.camera.capture_array()

        # Detect faces in the image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) == 0:
            self.recognition_label.setText("No face detected.")
            return

        face = faces[0]  # Process the first detected face
        landmarks = predictor(gray, face)
        face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)
        np_face_descriptor = np.array(face_descriptor)

        # Compare with known face descriptors
        min_distance = float('inf')
        matched_name = "Unknown"
        matched_employee_id = None

        for i, known_face_descriptor in enumerate(self.known_face_descriptors):
            distance = np.linalg.norm(known_face_descriptor - np_face_descriptor)
            if distance < min_distance:
                min_distance = distance
                matched_name = self.known_names[i]
                matched_employee_id = self.known_employee_ids[i]

        # Set a threshold for considering a face as recognized (e.g., 0.6)
        if min_distance < 0.6:
            name = matched_name
        else:
            name = "Unknown"
            matched_employee_id = None

        self.recognition_label.setText(f"Recognized: {name}")

        # Store the log in the database if recognized
        if matched_employee_id:
            room = session.query(room_table).filter_by(ip_address=self.ip_address).first()
            if room:
                log_entry = log_table.insert().values(
                    employee_id=matched_employee_id,
                    room_number=room.room_number,
                    date_and_time=datetime.now()  # Provide an explicit value for the date_and_time column
                )
                session.execute(log_entry)
                session.commit()
                
                # Open the door
                self.open_door()

    def open_door(self):
        os.system("sudo pigpiod")
        sleep(1)

        pi = pigpio.pi()
        if not pi.connected:
            self.recognition_label.setText("Failed to connect to the servo motor.")
            return
        
        SERVO_PIN = 18
        def set_servo_pulsewidth(pulsewidth):
            pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)

        try:
            # Open the door (set servo to open position)
            set_servo_pulsewidth(2500)
            sleep(60)  # Wait for 1 minute
            # Close the door (set servo to close position)
            set_servo_pulsewidth(500)
            sleep(2)
        finally:
            pi.set_servo_pulsewidth(SERVO_PIN, 0)
            pi.stop()
            os.system("sudo killall pigpiod")

            # Open the door
            set_servo_pulsewidth(2500)  # Adjust this value if needed
            QTimer.singleShot(60000, self.close_door)  # Close door after 1 minute

    def close_door(self):
        set_servo_pulsewidth(500)  # Adjust this value if needed
        sleep(2)
        set_servo_pulsewidth(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
