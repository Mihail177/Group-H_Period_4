import sys
import socket
import cv2
import dlib
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit
from PyQt5.QtGui import QPalette, QBrush, QLinearGradient, QColor
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker

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

# Reflect the employee table
employee_table = Table('EMPLOYEE', metadata, autoload_with=engine)
room_table = Table('ROOM', metadata, autoload_with=engine)

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

    def check_room_exists(self, mac_address):
        query = session.query(room_table).filter_by(mac_address=mac_address).first()
        return query is not None

    def register_room(self):
        room_number = self.room_input.text()
        if room_number:
            new_room = room_table.insert().values(room_number=room_number, mac_address=self.ip_address)
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

    def run_facial_recognition(self):
        # Prepare known face descriptors
        known_face_descriptors = []
        known_names = []

        employees = session.query(employee_table).all()
        for employee in employees:
            face_descriptor_blob = employee.facial_data
            face_descriptor = np.frombuffer(face_descriptor_blob, dtype=np.float64)  # Adjust this line based on how your data is stored
            known_face_descriptors.append(face_descriptor)
            full_name = f"{employee.first_name} {employee.last_name}"  # Concatenate first and last name
            known_names.append(full_name)

        # Open a connection to the webcam
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)

            for face in faces:
                landmarks = predictor(gray, face)
                face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)
                np_face_descriptor = np.array(face_descriptor)

                # Compare with known face descriptors
                min_distance = float('inf')
                matched_name = "Unknown"

                for i, known_face_descriptor in enumerate(known_face_descriptors):
                    distance = np.linalg.norm(known_face_descriptor - np_face_descriptor)
                    if distance < min_distance:
                        min_distance = distance
                        matched_name = known_names[i]

                # Set a threshold for considering a face as recognized (e.g., 0.6)
                if min_distance < 0.6:
                    name = matched_name
                    print(f"Face matches with distance {min_distance:.2f}. You now have access to the room, {name}.")
                else:
                    name = "Unknown"
                    print("Face does not match. Access denied.")

                # Draw a rectangle around the face and label it
                x, y, w, h = (face.left(), face.top(), face.width(), face.height())
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            cv2.imshow('Facial Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
