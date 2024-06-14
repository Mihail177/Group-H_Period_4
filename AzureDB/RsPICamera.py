import sys
import socket
import cv2
import dlib
import pigpio
import os
from time import sleep
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit
from PyQt5.QtGui import QPalette, QBrush, QLinearGradient, QColor
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from picamera2 import Picamera2

# Constants
SERVO_PIN = 18
SERVO_OPEN_PULSEWIDTH = 2500
SERVO_CLOSE_PULSEWIDTH = 500
PIGPIO_DAEMON_START_CMD = "sudo pigpiod"
PIGPIO_DAEMON_STOP_CMD = "sudo killall pigpiod"
PI_GPIO_WAIT_TIME = 1
FACIAL_RECOGNITION_THRESHOLD = 0.6
DB_CREDENTIALS = {
    "server": 'facesystemlock.database.windows.net',
    "database": 'facesystemlock',
    "username": 'superadmin',
    "password": 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'
}

# Paths to the model files
PREDICTOR_PATH = 'shape_predictor_68_face_landmarks.dat'
FACE_REC_MODEL_PATH = 'dlib_face_recognition_resnet_model_v1.dat'

# Initialize the face detector, shape predictor, and face recognition model
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)
face_rec_model = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH)

# Create SQLAlchemy engine and session
connection_string = f"mssql+pymssql://{DB_CREDENTIALS['username']}:{DB_CREDENTIALS['password']}@{DB_CREDENTIALS['server']}:1433/{DB_CREDENTIALS['database']}"
engine = create_engine(connection_string)
metadata = MetaData()
employee_table = Table('EMPLOYEE', metadata, autoload_with=engine)
room_table = Table('ROOM', metadata, autoload_with=engine)
log_table = Table('LOG', metadata, autoload_with=engine)
Session = sessionmaker(bind=engine)
session = Session()

def get_ip_address():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    return ip_address

class ServoController:
    def __init__(self, pin, open_pulsewidth, close_pulsewidth):
        self.pin = pin
        self.open_pulsewidth = open_pulsewidth
        self.close_pulsewidth = close_pulsewidth
        self.pi = pigpio.pi()

    def start(self):
        os.system(PIGPIO_DAEMON_START_CMD)
        sleep(PI_GPIO_WAIT_TIME)
        if not self.pi.connected:
            raise Exception("Failed to connect to pigpiod")

    def stop(self):
        self.pi.set_servo_pulsewidth(self.pin, 0)
        self.pi.stop()
        os.system(PIGPIO_DAEMON_STOP_CMD)

    def set_servo_pulsewidth(self, pulsewidth):
        self.pi.set_servo_pulsewidth(self.pin, pulsewidth)

    def open_door(self, open_duration=60):
        try:
            self.set_servo_pulsewidth(self.open_pulsewidth)
            sleep(open_duration)
            self.set_servo_pulsewidth(self.close_pulsewidth)
            sleep(2)
        finally:
            self.stop()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Room Registration")
        self.setGeometry(100, 100, 800, 480)
        self.setup_ui()
        self.ip_address = get_ip_address()
        if self.check_room_exists(self.ip_address):
            self.show_main_menu()
        self.servo_controller = ServoController(SERVO_PIN, SERVO_OPEN_PULSEWIDTH, SERVO_CLOSE_PULSEWIDTH)

    def setup_ui(self):
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.StretchToDeviceMode)
        gradient.setColorAt(0.0, QColor(128, 0, 128))
        gradient.setColorAt(1.0, QColor(0, 0, 255))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def check_room_exists(self, ip_address):
        return session.query(room_table).filter_by(ip_address=ip_address).first() is not None

    def register_room(self):
        room_number = self.room_input.text()
        if room_number:
            session.execute(room_table.insert().values(room_number=room_number, ip_address=self.ip_address))
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
        self.facial_button = self.create_button("Facial Recognition", self.run_facial_recognition)
        self.layout.addWidget(self.facial_button)
        self.nfc_button = self.create_button("NFC", self.run_nfc)
        self.layout.addWidget(self.nfc_button)
        self.recognition_label = QLabel(self)
        self.recognition_label.setStyleSheet("font-size: 18px; color: white;")
        self.recognition_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.recognition_label)

    def create_button(self, text, handler):
        button = QPushButton(text, self)
        button.setFixedSize(200, 50)
        button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px;")
        button.clicked.connect(handler)
        return button

    def run_nfc(self):
        # Implement NFC functionality here
        pass

    def run_facial_recognition(self):
        known_face_descriptors, known_names, known_employee_ids = self.load_known_faces()
        frame = self.capture_image()
        if frame is None:
            self.recognition_label.setText("Failed to capture image.")
            return
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        if len(faces) == 0:
            self.recognition_label.setText("No face detected.")
            return
        matched_name, matched_employee_id = self.recognize_face(faces[0], frame, known_face_descriptors, known_names, known_employee_ids)
        self.recognition_label.setText(f"Recognized: {matched_name}")
        if matched_employee_id:
            self.log_access(matched_employee_id)
            self.servo_controller.open_door()

    def load_known_faces(self):
        known_face_descriptors, known_names, known_employee_ids = [], [], []
        for employee in session.query(employee_table).all():
            face_descriptor = np.frombuffer(employee.facial_data, dtype=np.float64)
            known_face_descriptors.append(face_descriptor)
            known_names.append(f"{employee.first_name} {employee.last_name}")
            known_employee_ids.append(employee.employee_id)
        return known_face_descriptors, known_names, known_employee_ids

    def capture_image(self):
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration())
        picam2.start()
        frame = picam2.capture_array()
        picam2.stop()
        return frame

    def recognize_face(self, face, frame, known_face_descriptors, known_names, known_employee_ids):
        landmarks = predictor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), face)
        face_descriptor = np.array(face_rec_model.compute_face_descriptor(frame, landmarks))
        min_distance, matched_name, matched_employee_id = float('inf'), "Unknown", None
        for known_face_descriptor, name, emp_id in zip(known_face_descriptors, known_names, known_employee_ids):
            distance = np.linalg.norm(known_face_descriptor - face_descriptor)
            if distance < min_distance:
                min_distance, matched_name, matched_employee_id = distance, name, emp_id
        if min_distance >= FACIAL_RECOGNITION_THRESHOLD:
            matched_name, matched_employee_id = "Unknown", None
        return matched_name, matched_employee_id

    def log_access(self, employee_id):
        room = session.query(room_table).filter_by(ip_address=self.ip_address).first()
        if room:
            session.execute(log_table.insert().values(employee_id=employee_id, room_number=room.room_number, date_and_time=datetime.now()))
            session.commit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
