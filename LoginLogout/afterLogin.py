import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, \
    QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QLineEdit, \
    QFormLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import face_recognition
from PyQt5.QtGui import QFontDatabase, QFont, QIcon
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker


class AfterLoginWindow(QMainWindow):
    def __init__(self, settings, login_window):
        super().__init__()
        self.label_image = None
        self.settings = settings
        self.login_window = login_window
        self.initUI()

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

    def initUI(self):
        self.setWindowTitle("After Login")
        self.setGeometry(100, 100, 1200, 600)
        self.setStyleSheet(self.get_stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left side layout
        left_layout = QVBoxLayout()

        # Add a logout button
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet(
            "background-color: #FF6347; color: white; border-radius: 15px; font-family: Baloo 2; font-weight: bold; height: 60px")
        logout_button.clicked.connect(self.logout)

        choose_file_button = QPushButton("Choose File")
        choose_file_button.clicked.connect(self.choose_file)

        # Add and Remove buttons
        add_button = QPushButton("Add Employee")
        add_button.clicked.connect(self.open_add_employee_form)
        remove_button = QPushButton("Remove Employee")
        remove_button.clicked.connect(self.remove_employee)

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

        left_layout.addWidget(add_button)
        left_layout.addWidget(remove_button)
        left_layout.addWidget(logout_button)
        left_layout.addWidget(choose_file_button)

        left_layout.addStretch()  # Add a stretch to push the buttons to the top

        # Center layout
        center_layout = QVBoxLayout()

        # Table to display employee data
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Employee ID', 'First Name', 'Last Name', 'Facial Data', 'NFC Data'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        center_layout.addWidget(self.table)

        # Right side layout (empty for now, reserved for future use)
        right_layout = QVBoxLayout()
        right_layout.addStretch()  # Add a stretch to make it occupy space

        # Add the layouts to the main layout with spacers
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(center_layout, 3)  # Center layout takes 3 parts of the grid
        main_layout.addLayout(right_layout, 1)  # Right layout takes 1 part of the grid

    def logout(self):
        # Clear the saved credentials
        self.settings.remove("email")
        self.settings.remove("password")
        QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()
        self.login_window.show()

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
                self.table.setItem(row_idx, 3,
                                   QTableWidgetItem("Facial Data Present" if row.facial_data else "No Facial Data"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(row.NFC_data))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

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
        self.table.setHorizontalHeaderLabels(['Email', 'Password'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.admin_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(row.email))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row.password))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def load_log_data(self):
        self.table.clear()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Date', 'Time', 'Room Number', 'Employee ID'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.log_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.date)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row.time)))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row.room_number)))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row.employee_id)))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def load_room_data(self):
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Room Number', 'Purpose', 'Access List'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.room_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(row.room_number))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row.purpose))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row.access_list))
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
        finally:
            session.close()

    def remove_employee(self):
        employee_id, ok = QInputDialog.getText(self, 'Remove Employee', 'Enter Employee ID:')
        if ok:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            try:
                employee = session.query(self.employee_table).filter_by(employee_id=employee_id).first()
                if employee:
                    session.delete(employee)
                    session.commit()
                    QMessageBox.information(self, "Remove Employee", "Employee removed successfully!")
                    self.load_employee_data()
                else:
                    QMessageBox.warning(self, "Remove Employee", "Employee not found!")
            except Exception as e:
                session.rollback()
                QMessageBox.warning(self, "Database Error", f"An error occurred: {e}")
            finally:
                session.close()

    def open_add_employee_form(self):
        self.add_employee_form = QWidget()
        self.add_employee_form.setWindowTitle("Add Employee")
        self.add_employee_form.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.input_id = QLineEdit()
        self.input_first_name = QLineEdit()
        self.input_last_name = QLineEdit()
        self.input_nfc_data = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("Employee ID:", self.input_id)
        form_layout.addRow("First Name:", self.input_first_name)
        form_layout.addRow("Last Name:", self.input_last_name)
        form_layout.addRow("NFC Data:", self.input_nfc_data)

        self.label_image = QLabel()
        self.label_image.setFixedSize(200, 200)
        self.label_image.setAlignment(Qt.AlignCenter)
        form_layout.addRow("Image:", self.label_image)

        choose_file_button = QPushButton("Choose File")
        choose_file_button.clicked.connect(self.choose_file)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_data)

        layout.addLayout(form_layout)
        layout.addWidget(choose_file_button)
        layout.addWidget(submit_button)

        self.add_employee_form.setLayout(layout)
        self.add_employee_form.show()

    def get_stylesheet(self):
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QLabel {
            font-family: Baloo 2;
            font-size: 18px;
        }
        QLineEdit {
            padding: 5px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QPushButton {
            padding: 10px 15px;
            font-size: 16px;
            background-color: #008CBA;
            color: white;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #005f75;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 14px;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            padding: 5px;
            border: none;
            font-size: 14px;
            font-family: Baloo 2;
        }
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = QMainWindow()  # Placeholder for actual login window
    window = AfterLoginWindow(None, login_window)
    window.show()
    sys.exit(app.exec_())
