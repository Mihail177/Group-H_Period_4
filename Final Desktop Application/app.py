import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, \
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QLineEdit, \
    QFormLayout, QListWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import face_recognition
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker


class EmployeeManagementWindow(QMainWindow):
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
        self.password = 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'

        # Define the connection string
        self.connection_string = f'mssql+pymssql://{self.username}:{self.password}@{self.server}:1433/{self.database}'

        # Create an SQLAlchemy engine
        self.engine = create_engine(self.connection_string)

        # Define metadata
        self.metadata = MetaData()

        # Reflect the tables
        self.employee_table = Table('EMPLOYEE', self.metadata, autoload_with=self.engine)
        self.log_table = Table('LOG', self.metadata, autoload_with=self.engine)
        self.room_table = Table('ROOM', self.metadata, autoload_with=self.engine)

        # Load data for initial menu item
        self.load_selected_table(self.menu.item(0), None)

    def initUI(self):
        self.setWindowTitle("Employee Management System")
        self.setGeometry(100, 100, 1200, 600)
        self.setStyleSheet(self.get_stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left side layout
        left_layout = QVBoxLayout()

        # Vertical menu
        self.menu = QListWidget()
        self.menu.addItems(["Employee", "Log", "Room"])
        self.menu.currentItemChanged.connect(self.load_selected_table)

        # Add a logout button
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("background-color: red; color: white; border-radius: 15px; font-family: Berkshire Swash; font-weight: bold; height: 60px")
        logout_button.clicked.connect(self.logout)

        # Add and Remove buttons
        self.add_button = QPushButton("Add Employee")
        self.add_button.clicked.connect(self.open_add_employee_form)
        self.remove_button = QPushButton("Remove Employee")
        self.remove_button.clicked.connect(self.remove_employee)

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

        left_layout.addWidget(self.add_button)
        left_layout.addWidget(self.remove_button)
        left_layout.addWidget(logout_button)

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
        right_layout.addWidget(self.menu)
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
                        self.load_employee_data()  # Reload the data to reflect the changes
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

    def load_selected_table(self, current, previous):
        if current:
            table_name = current.text().lower()
            if table_name == "employee":
                self.load_employee_data()
                self.add_button.setVisible(True)
                self.remove_button.setVisible(True)
            elif table_name == "log":
                self.load_log_data()
                self.add_button.setVisible(False)
                self.remove_button.setVisible(False)
            elif table_name == "room":
                self.load_room_data()
                self.add_button.setVisible(False)
                self.remove_button.setVisible(False)

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
                self.table.setItem(row_idx, 3, QTableWidgetItem("Facial Data Present" if row.facial_data else "No Facial Data"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(row.NFC_data))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred while loading employee data: {e}")
        finally:
            session.close()

    def load_log_data(self):
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Employee ID', 'Room Number', 'Date and Time'])
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            result = session.query(self.log_table).all()
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row.employee_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row.room_number)))
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
        self.add_employee_form = QWidget()
        self.add_employee_form.setWindowTitle("Add Employee")
        self.add_employee_form.setGeometry(100, 100, 400, 300)

        self.add_employee_form.setStyleSheet("""
                   QWidget {
                       background: qlineargradient(
                           spread:pad, x1:0, y1:0, x2:1, y2:1, 
                           stop:0 #9C87E1, stop:1 #FCE3FD);
                       font-family: 'Baloo 2';
                       color: black;
                   }
                   QLineEdit, QComboBox {
                       background-color: white;
                       padding: 10px;
                       border: 1px solid #DDDDDD;
                       border-radius: 15px;
                       font-family: 'Baloo 2';
                       font-size: 16px;
                       color: black;
                   }
                   QLabel {
                       background: transparent;
                       font-family: 'Baloo 2';
                       font-size: 16px;
                       font-weight: bold;
                       color: white;
                   }
                   QPushButton {
                       background-color: #9C87E1;
                       color: white;
                       border: none;
                       padding: 10px 20px;
                       border-radius: 15px;
                       font-family: 'Baloo 2';
                       font-size: 18px;
                       font-weight: bold;
                       height: 60px;
                   }
                   QPushButton:hover {
                       background: qlineargradient(
                           spread:pad, x1:0, y1:0, x2:1, y2:1, 
                           stop:0 #9C87E1, stop:1 #FCE3FD);        
                   }
                   """)

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
        QWidget {
        background: qlineargradient(
            spread:pad, x1:0, y1:0, x2:1, y2:1, 
            stop:0 #FCE3FD, stop:1 #9C87E1);
        }

        QListWidget {
            background-color: white;
            border: 1px solid #DDDDDD;
            padding: 10px;
            font-family: Baloo 2;
            font-size: 18px;
            font-weight: bold;
            border-radius: 15px;
            margin-bottom: 10px;
            height: 60px;
        }

        QListWidget::item {
            background-color: white;
            border: none;
            padding: 5px;
        }

        QListWidget::item:selected {
            background-color: #9C87E1;
            color: white;
            border-radius: 10px;
        }

        QPushButton {
            background-color: #9C87E1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 15px;
            font-family: Baloo 2;
            font-size: 18px;
            font-weight: bold;
            height: 60px;
        }

        QPushButton:hover {
            background: qlineargradient(
            spread:pad, x1:0, y1:0, x2:1, y2:1, 
            stop:0 #9C87E1, stop:1 #FCE3FD);        
        }

        QLineEdit, QComboBox {
            padding: 10px;
            border: 1px solid #DDDDDD;
            border-radius: 5px;
            font-family: Baloo 2;
            font-size: 16px;
        }

        QLabel {
            font-family: Baloo 2;
            font-size: 16px;
            font-weight: bold;
        }

        QTableWidget {
            background-color: white;
            border-radius: 7px;
            font-family: Baloo 2;
            font-size: 16px;
        }

        QHeaderView::section {
            background-color: #F0F0F0;
            padding: 5px;
            border: none;
        }
        """


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = QMainWindow()
    window = EmployeeManagementWindow(None, login_window)
    window.show()
    sys.exit(app.exec_())
