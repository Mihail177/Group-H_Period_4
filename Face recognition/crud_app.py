from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog, \
    QMessageBox, QLineEdit, QHBoxLayout, QFormLayout, QFrame, QSpacerItem, QSizePolicy, QTableWidget, \
    QTableWidgetItem, QHeaderView, QListWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap,QPainter, QLinearGradient, QColor, QBrush
import sys
import face_recognition
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker

class GradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#9C87E1"))
        gradient.setColorAt(1, QColor("#FCE3FD"))
        painter.fillRect(self.rect(), gradient)

class AddEmployeeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Employee")
        self.setGeometry(100, 100, 800, 600)

        # Create the gradient background widget
        self.gradient_widget = GradientWidget(self)
        self.setCentralWidget(self.gradient_widget)

        # Set up layout and other widgets
        layout = QVBoxLayout(self.gradient_widget)
        label = QLabel("Add Employee Form", self.gradient_widget)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

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

        frame_layout.addWidget(self.label_image, alignment=Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(choose_file_button, alignment=Qt.AlignmentFlag.AlignCenter)
        frame_layout.addLayout(form_layout)
        frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        frame_layout.addWidget(submit_button, alignment=Qt.AlignmentFlag.AlignCenter)

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


class EmployeeManagementWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee Management")
        self.setGeometry(100, 100, 1200, 600)
        self.setStyleSheet("background-color: #FCE3FD;")

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

        # Reflect tables
        self.employee_table = Table('EMPLOYEE', self.metadata, autoload_with=self.engine)
        self.admin_table = Table('ADMIN', self.metadata, autoload_with=self.engine)
        self.log_table = Table('LOG', self.metadata, autoload_with=self.engine)
        self.room_table = Table('ROOM', self.metadata, autoload_with=self.engine)

        # Load data for initial menu item
        self.load_selected_table(self.menu.item(0), None)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Vertical menu
        self.menu = QListWidget()
        self.menu.addItems(["Employee", "Admin", "Log", "Room"])
        self.menu.currentItemChanged.connect(self.load_selected_table)

        # Table to display data
        self.table = QTableWidget()

        # Add and Remove buttons
        self.button_layout = QVBoxLayout()
        self.add_button = QPushButton("Add Employee")
        self.add_button.clicked.connect(self.open_add_employee_form)
        self.remove_button = QPushButton("Remove Employee")
        self.remove_button.clicked.connect(self.remove_employee)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.remove_button)

        main_layout.addWidget(self.menu)
        main_layout.addLayout(self.button_layout)
        main_layout.addWidget(self.table)

        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def load_selected_table(self, current, previous):
        table_name = current.text().lower()
        if table_name == "employee":
            self.load_employee_data()
            self.add_button.setVisible(True)
            self.remove_button.setVisible(True)
        else:
            self.add_button.setVisible(False)
            self.remove_button.setVisible(True)
            if table_name == "admin":
                self.load_admin_data()
            elif table_name == "log":
                self.load_log_data()
            elif table_name == "room":
                self.load_room_data()

    def load_employee_data(self):
        self.table.clear()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Employee ID', 'First Name', 'Last Name', 'Facial Data', 'NFC Data'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.employee_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.employee_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row.first_name))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row.last_name))
                self.table.setItem(row_idx, 3,
                                   QTableWidgetItem("Facial Data Present" if row.facial_data else "No Facial Data"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(row.NFC_data))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def load_admin_data(self):
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Email Address', 'Password'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.admin_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(row.email_address))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row.password))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def load_log_data(self):
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Employee ID', 'IP Address', 'Date and Time'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.log_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.employee_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row.ip_address))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row.date_and_time)))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def load_room_data(self):
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['IP Address', 'Room Number'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.room_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(row.ip_address))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row.room_number)))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def open_add_employee_form(self):
        self.add_employee_window = AddEmployeeWindow()
        self.add_employee_window.show()

    def remove_employee(self):
        current_row = self.table.currentRow()
        if current_row != -1:
            employee_id_item = self.table.item(current_row, 0)
            if employee_id_item:
                employee_id = employee_id_item.text()
                Session = sessionmaker(bind=self.engine)
                session = Session()
                try:
                    delete_query = self.employee_table.delete().where(self.employee_table.c.employee_id == employee_id)
                    session.execute(delete_query)
                    session.commit()
                    QMessageBox.information(self, "Success", "Employee removed successfully!")
                    self.load_employee_data()
                except Exception as e:
                    session.rollback()
                    QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
                finally:
                    session.close()
        else:
            QMessageBox.warning(self, "Selection Error", "Please select an employee to remove.")


def main():
    app = QApplication(sys.argv)
    window = EmployeeManagementWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
