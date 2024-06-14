import sys
import socket
import dlib
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit
from PyQt5.QtGui import QPalette, QBrush, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QTimer
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import cv2
import os
import pigpio
from time import sleep
from datetime import datetime

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
password = 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'

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
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.StretchToDeviceMode)
        gradient.setColorAt(0.0, QColor(128, 0, 128))  # Purple
        gradient.setColorAt(1.0, QColor(0, 0, 255))  # Blue
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        self.ip_address = get_ip_address()
        room_exists = self.check_room_exists(self.ip_address)

        self.layout = QVBoxLayout()
        # Center the layout
        self.layout.setAlignment(Qt.AlignCenter)

        if not room_exists:
            self.room_input = QLineEdit(self)
            self.room_input.setPlaceholderText("Enter Room Number")
            self.room_input.setFixedSize(200, 50)
            self.room_input.setStyleSheet("background-color: white; font-size: 18px; color: black;")
            self.layout.addWidget(self.room_input)

            self.submit_button = QPushButton("Submit", self)
            self.submit_button.setFixedSize(200, 50)
            self.submit_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px;")
            self.submit_button.clicked.connect(self.register_room)
            self.layout.addWidget(self.submit_button)

            self.message_label = QLabel(self)
            self.message_label.setStyleSheet("font-size: 14px; color: white;")
            self.message_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.message_label)
        else:
            self.show_main_menu()

        self.setLayout(self.layout)

    def check_room_exists(self, ip_address):
        query = session.query(room_table).filter_by(ip_address=ip_address).first()
        return query is not None

    def register_room(self):
        room_number = self.room_input.text()
        if room_number:
            new_room = room_table.insert().values(room_number=room_number, ip_address=self.ip_address)
            session.execute(new_room)
            session.commit()
            self.message_label.setText(f"Room {room_number} registered successfully with IP {self.ip_address}.")
            self.show_main_menu()
        else:
            self.message_label.setText("Please enter a valid room number.")

    def show_main_menu(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.facial_button = QPushButton("Facial Recognition", self)
        self.facial_button.setFixedSize(200, 50)
        self.facial_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px;")
        self.facial_button.clicked.connect(self.run_facial_recognition)
        self.layout.addWidget(self.facial_button)

        self.nfc_button = QPushButton("NFC", self)
        self.nfc_button.setFixedSize(200, 50)
        self.nfc_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 18px;")
        # Connect NFC functionality here
        self.layout.addWidget(self.nfc_button)

        self.result_label = QLabel(self)
        self.result_label.setStyleSheet("font-size: 14px; color: white;")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.result_label)

    def run_facial_recognition(self):
        # Prepare known face descriptors
        known_face_descriptors = []
        known_names = []
        known_ids = []

        employees = session.query(employee_table).all()
        for employee in employees:
            face_descriptor_blob = employee.facial_data
            face_descriptor = np.frombuffer(face_descriptor_blob, dtype=np.float64)  # Adjust this line based on how your data is stored
            known_face_descriptors.append(face_descriptor)
            full_name = f"{employee.first_name} {employee.last_name}"  # Concatenate first and last name
            known_names.append(full_name)
            known_ids.append(employee.id)

        # Initialize Picamera2
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
        picam2.configure(config)
        picam2.start()

        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        recognized_name = "Unknown"
        recognized_id = None

        for face in faces:
            landmarks = predictor(gray, face)
            face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)
            np_face_descriptor = np.array(face_descriptor)

            # Compare with known face descriptors
            min_distance = float('inf')
            matched_name = "Unknown"
            matched_id = None

            for i, known_face_descriptor in enumerate(known_face_descriptors):
                distance = np.linalg.norm(known_face_descriptor - np_face_descriptor)
                if distance < min_distance:
                    min_distance = distance
                    matched_name = known_names[i]
                    matched_id = known_ids[i]

            # Set a threshold for considering a face as recognized (e.g., 0.6)
            if min_distance < 0.6:
                recognized_name = matched_name
                recognized_id = matched_id
                self.result_label.setText(f"Recognized {recognized_name}. Access granted.")
                self.log_access(recognized_id)
                self.open_door()
            else:
                self.result_label.setText("Face does not match. Access denied.")
                
        picam2.stop()

    def log_access(self, employee_id):
        room_number = session.query(room_table).filter_by(ip_address=self.ip_address).first().room_number
        current_time = datetime.now()
        new_log = log_table.insert().values(employee_id=employee_id, room_number=room_number, timestamp=current_time)
        session.execute(new_log)
        session.commit()

    def open_door(self):
        os.system("sudo pigpiod")
        sleep(1)  # Wait a bit to ensure pigpiod has started

        pi = pigpio.pi()
        if not pi.connected:
            print("not connected")
            return

        SERVO_PIN = 18
        pi.set_servo_pulsewidth(SERVO_PIN, 1500)  # Open the door
        QTimer.singleShot(60000, self.close_door)  # Close the door after 1 minute

    def close_door(self):
        pi = pigpio.pi()
        if pi.connected:
            SERVO_PIN = 18
            pi.set_servo_pulsewidth(SERVO_PIN, 500)  # Close the door
            sleep(2)
            pi.set_servo_pulsewidth(SERVO_PIN, 0)
            pi.stop()
            os.system("sudo killall pigpiod")
        self.reset_to_main()

    def reset_to_main(self):
        self.result_label.clear()
        self.show_main_menu()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
