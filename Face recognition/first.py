from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout, QFormLayout, QFrame
from PyQt6.QtGui import QPixmap, QColor, QPalette
from PyQt6.QtCore import Qt
import os
import sys
import face_recognition
import numpy as np
import mysql.connector
from db_config import db_config

class UploadImageWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upload Image")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #E6E6FA;")  # Lilac background color

        self.setup_ui()

        # Initialize file_path variable to store selected file path
        self.file_path = None

    def setup_ui(self):
        # Create widgets
        self.label_image = QLabel()
        self.label_image.setFixedSize(300, 300)
        self.label_image.setStyleSheet("border: 2px solid #8A2BE2;")  # Lilac border color
        self.label_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_choose_file = QPushButton("Choose File")
        self.button_choose_file.clicked.connect(self.choose_file)
        self.button_choose_file.setStyleSheet(self.get_button_style())

        self.button_submit = QPushButton("Submit")
        self.button_submit.clicked.connect(self.submit_data)
        self.button_submit.setStyleSheet(self.get_button_style())

        self.input_id = QLineEdit()
        self.input_name = QLineEdit()
        self.input_age = QLineEdit()

        self.set_input_style(self.input_id, "ID")
        self.set_input_style(self.input_name, "Name")
        self.set_input_style(self.input_age, "Age")

        # Set up layouts
        form_layout = QFormLayout()
        form_layout.addRow("ID:", self.input_id)
        form_layout.addRow("Name:", self.input_name)
        form_layout.addRow("Age:", self.input_age)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.button_choose_file)
        button_layout.addWidget(self.button_submit)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        right_layout = QVBoxLayout()
        right_layout.addLayout(form_layout)
        right_layout.addLayout(button_layout)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label_image)
        main_layout.addLayout(right_layout)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def set_input_style(self, input_field, placeholder):
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #8A2BE2;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #BA55D3;
            }
        """)

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #8A2BE2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #BA55D3;
            }
        """

    def choose_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.jpg *.jpeg *.png)")
        if file_dialog.exec():
            self.file_path = file_dialog.selectedFiles()[0]
            pixmap = QPixmap(self.file_path)
            pixmap = pixmap.scaledToWidth(300)
            self.label_image.setPixmap(pixmap)

    def submit_data(self):
        if self.file_path:
            id_ = self.input_id.text()
            name = self.input_name.text()
            age = self.input_age.text()

            if id_ and name and age:
                # Load image and extract facial encoding
                image = face_recognition.load_image_file(self.file_path)
                face_encodings = face_recognition.face_encodings(image)

                if face_encodings:
                    facial_encoding = face_encodings[0]
                    facial_encoding_binary = facial_encoding.tobytes()

                    # Connect to the database
                    conn = mysql.connector.connect(**db_config)
                    cursor = conn.cursor()

                    # Insert data into database
                    cursor.execute('''
                        INSERT INTO employees (id, name, age, facial_data)
                        VALUES (%s, %s, %s, %s)
                    ''', (id_, name, age, facial_encoding_binary))

                    conn.commit()
                    conn.close()

                    QMessageBox.information(self, "Submission Confirmation", "Data submitted successfully!")
                else:
                    QMessageBox.warning(self, "Face Not Found", "No face found in the selected image.")
            else:
                QMessageBox.warning(self, "Incomplete Information", "Please provide ID, name, and age.")
        else:
            QMessageBox.warning(self, "No File Selected", "Please select a file first.")

def main():
    app = QApplication(sys.argv)
    window = UploadImageWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
