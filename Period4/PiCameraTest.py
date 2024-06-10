import sys
import cv2
import dlib
import numpy as np
import pickle
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtGui import QPalette, QBrush, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class FacialRecognitionThread(QThread):
    update_label = pyqtSignal(str)
    update_image = pyqtSignal(np.ndarray)

    def run(self):
        # Paths to the model files
        predictor_path = 'shape_predictor_68_face_landmarks.dat'
        face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'

        # Initialize the face detector, shape predictor, and face recognition model
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(predictor_path)
        face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)

        # Load the stored embedding
        with open('embeddings/cristian.pickle', 'rb') as f:
            user_data = pickle.load(f)
        known_face_descriptor = user_data['face_descriptor']
        known_name = user_data['name']

        # Open a connection to the Pi Camera
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)

            name = "Unknown"
            for face in faces:
                landmarks = predictor(gray, face)
                face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)
                np_face_descriptor = np.array(face_descriptor)

                # Calculate the Euclidean distance between the known face and the detected face
                distance = np.linalg.norm(known_face_descriptor - np_face_descriptor)
                print(f"Distance: {distance}")

                # Set a threshold for considering a face as recognized (e.g., 0.6)
                if distance < 0.6:
                    name = known_name
                    print(f"Face matches. You now have access to the room, {name}.")
                else:
                    print("Face does not match. Access denied.")

                # Draw a rectangle around the face and label it
                x, y, w, h = (face.left(), face.top(), face.width(), face.height())
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            self.update_image.emit(frame)
            self.update_label.emit(f"Recognition Result: {name}")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Raspberry Pi App")
        self.setGeometry(100, 100, 800, 480)

        # Remove window decorations and set full screen
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.showFullScreen()

        # Create a gradient background
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.StretchToDeviceMode)
        gradient.setColorAt(0.0, QColor(128, 0, 128))  # Purple
        gradient.setColorAt(1.0, QColor(0, 0, 255))  # Blue
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        layout = QVBoxLayout()

        # Center the layout
        layout.setAlignment(Qt.AlignCenter)

        # Create and style buttons
        self.facial_button = QPushButton("Facial Recognition", self)
        self.facial_button.setFixedSize(200, 50)
        self.facial_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px;")
        self.facial_button.clicked.connect(self.facial_recognition)
        layout.addWidget(self.facial_button)

        self.nfc_button = QPushButton("NFC", self)
        self.nfc_button.setFixedSize(200, 50)
        self.nfc_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 18px;")
        self.nfc_button.clicked.connect(self.nfc)
        layout.addWidget(self.nfc_button)

        # Style the message label
        self.message_label = QLabel(self)
        self.message_label.setStyleSheet("font-size: 14px; color: white;")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def facial_recognition(self):
        self.message_label.setText("Starting facial recognition...")
        self.recognition_thread = FacialRecognitionThread()
        self.recognition_thread.update_label.connect(self.update_message_label)
        self.recognition_thread.update_image.connect(self.update_image)
        self.recognition_thread.start()

    def nfc(self):
        self.message_label.setText("NFC functionality is not implemented yet.")

    def update_message_label(self, text):
        self.message_label.setText(text)

    def update_image(self, frame):
        # Convert frame to QImage and display it in QLabel (not implemented here)
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
