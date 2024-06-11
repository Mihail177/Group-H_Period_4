from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog, \
    QMessageBox, QLineEdit, QHBoxLayout, QFormLayout, QFrame, QSpacerItem, QSizePolicy, QTableWidget, QTableWidgetItem, \
    QHeaderView
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect
import sys
import face_recognition
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker

class AddEmployeeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Employee")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(self.get_stylesheet())

        self.setup_ui()

        # Initialize file_path variable to store selected file path
        self.file_path = None

        # Define your database credentials
        self.server = 'facesystemlock.database.windows.net'
        self.database = 'facesystemlock'
        self.username = 'superadmin'
        self.password = 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'  # Ensure this is the correct password

        # Define the connection string
        self.connection_string = f'mssql+pymssql://{self.username}:{self.password}@{self.server}:1433/{self.database}'

        # Create an SQLAlchemy engine
        self.engine = create_engine(self.connection_string)

        # Define metadata
        self.metadata = MetaData()

        # Reflect the employee table
        self.employee_table = Table('EMPLOYEE', self.metadata, autoload_with=self.engine)

    def setup_ui(self):
        # Create widgets
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)

        self.label_image = QLabel()
        self.label_image.setFixedSize(300, 300)
        self.label_image.setStyleSheet("border: 2px solid #E637BF; border-radius: 10px;")
        self.label_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        choose_file_button = QPushButton("Choose File")
        choose_file_button.clicked.connect(self.choose_file)

        self.input_id = QLineEdit()
        self.input_first_name = QLineEdit()
        self.input_last_name = QLineEdit()
        self.input_nfc_data = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("Employee ID:", self.input_id)
        form_layout.addRow("First Name:", self.input_first_name)
        form_layout.addRow("Last Name:", self.input_last_name)
        form_layout.addRow("NFC Data:", self.input_nfc_data)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_data)

        frame_layout.addWidget(self.label_image)
        frame_layout.addWidget(choose_file_button)
        frame_layout.addLayout(form_layout)
        frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        frame_layout.addWidget(submit_button, alignment=Qt.AlignmentFlag.AlignBottom)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.addStretch()
        main_layout.addWidget(frame)
        main_layout.addStretch()

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
            employee_id = self.input_id.text()
            first_name = self.input_first_name.text()
            last_name = self.input_last_name.text()
            nfc_data = self.input_nfc_data.text()

            if employee_id and first_name and last_name and nfc_data:
                # Load image and extract facial encoding
                image = face_recognition.load_image_file(self.file_path)
                face_encodings = face_recognition.face_encodings(image)

                if face_encodings:
                    facial_encoding = face_encodings[0]
                    facial_encoding_binary = facial_encoding.tobytes()

                    # Connect to the database and insert data
                    Session = sessionmaker(bind=self.engine)
                    session = Session()

                    try:
                        # Insert data into database
                        new_employee = {
                            'employee_id': employee_id,
                            'first_name': first_name,
                            'last_name': last_name,
                            'facial_data': facial_encoding_binary,
                            'NFC_data': nfc_data
                        }
                        ins = self.employee_table.insert().values(new_employee)
                        session.execute(ins)
                        session.commit()

                        QMessageBox.information(self, "Submission Confirmation", "Data submitted successfully!")
                    except Exception as e:
                        session.rollback()
                        QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
                    finally:
                        session.close()
                else:
                    QMessageBox.warning(self, "Face Not Found", "No face found in the selected image.")
            else:
                QMessageBox.warning(self, "Incomplete Information", "Please provide all fields.")
        else:
            QMessageBox.warning(self, "No File Selected", "Please select a file first.")

    def get_stylesheet(self):
        return """
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #D2F1E4, stop: 1 #FBCAEF
                );  /* Gradient background */
            }
            QLabel, QPushButton, QLineEdit, QDateEdit, QTableWidget {
                color: #48304D;  /* Text color */
                font-family: 'Arial', sans-serif;  /* Arial font */
                font-size: 16px;
            }
            QLineEdit {
                background-color: #F865B0;  /* Background color for input fields */
                border: 2px solid #E637BF;  /* Border color */
                border-radius: 10px;
                padding: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
            }
            QLineEdit:focus {
                border: 2px solid #48304D;  /* Border color on focus */
            }
            QPushButton {
                background-color: #E637BF;  /* Button background color */
                border: none;
                border-radius: 10px;
                padding: 10px;
                margin-top: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
                color: white;  /* Button text color */
            }
            QPushButton:hover {
                background-color: #F865B0;  /* Button color on hover */
                box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.4);
            }
            QFrame {
                background-color: #FBCAEF;  /* Background color for frames */
                border-radius: 15px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
            }
            QTableWidget {
                background-color: #FFFFFF;  /* Table background color */
                border: 2px solid #E637BF;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #E637BF;
                color: white;
                padding: 5px;
                border: none;
            }
        """

class EmployeeManagementWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee Management")
        self.setGeometry(100, 100, 1200, 600)
        self.setStyleSheet(self.get_stylesheet())

        self.setup_ui()

        # Define your database credentials
        self.server = 'facesystemlock.database.windows.net'
        self.database = 'facesystemlock'
        self.username = 'superadmin'
        self.password = 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'  # Ensure this is the correct password

        # Define the connection string
        self.connection_string = f'mssql+pymssql://{self.username}:{self.password}@{self.server}:1433/{self.database}'

        # Create an SQLAlchemy engine
        self.engine = create_engine(self.connection_string)

        # Define metadata
        self.metadata = MetaData()

        # Reflect the employee table
        self.employee_table = Table('EMPLOYEE', self.metadata, autoload_with=self.engine)

        self.load_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Table to display employee data
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Employee ID', 'First Name', 'Last Name', 'Facial Data', 'NFC Data'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Add and Remove buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Employee")
        add_button.clicked.connect(self.open_add_employee_form)
        remove_button = QPushButton("Remove Employee")
        remove_button.clicked.connect(self.remove_employee)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)

        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

    def load_data(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.employee_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.employee_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row.first_name))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row.last_name))
                self.table.setItem(row_idx, 3, QTableWidgetItem("Facial Data Present" if row.facial_data else "No Facial Data"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(row.NFC_data))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def open_add_employee_form(self):
        self.add_employee_window = AddEmployeeWindow()
        self.add_employee_window.show()

    def remove_employee(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an employee to remove.")
            return

        selected_row = selected_items[0].row()
        employee_id = self.table.item(selected_row, 0).text()

        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            session.query(self.employee_table).filter_by(employee_id=employee_id).delete()
            session.commit()
            self.table.removeRow(selected_row)
            QMessageBox.information(self, "Employee Removed", "Employee removed successfully!")
        except Exception as e:
            session.rollback()
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def get_stylesheet(self):
        return """
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #D2F1E4, stop: 1 #FBCAEF
                );  /* Gradient background */
            }
            QLabel, QPushButton, QLineEdit, QDateEdit, QTableWidget {
                color: #48304D;  /* Text color */
                font-family: 'Arial', sans-serif;  /* Arial font */
                font-size: 16px;
            }
            QLineEdit {
                background-color: #F865B0;  /* Background color for input fields */
                border: 2px solid #E637BF;  /* Border color */
                border-radius: 10px;
                padding: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
            }
            QLineEdit:focus {
                border: 2px solid #48304D;  /* Border color on focus */
            }
            QPushButton {
                background-color: #E637BF;  /* Button background color */
                border: none;
                border-radius: 10px;
                padding: 10px;
                margin-top: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
                color: white;  /* Button text color */
            }
            QPushButton:hover {
                background-color: #F865B0;  /* Button color on hover */
                box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.4);
            }
            QFrame {
                background-color: #FBCAEF;  /* Background color for frames */
                border-radius: 15px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
            }
            QTableWidget {
                background-color: #FFFFFF;  /* Table background color */
                border: 2px solid #E637BF;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #E637BF;
                color: white;
                padding: 5px;
                border: none;
            }
        """

def main():
    app = QApplication(sys.argv)

    window = EmployeeManagementWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

