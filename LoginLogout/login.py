import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, \
    QMessageBox, QCheckBox
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPixmap, QFontDatabase, QFont, QBrush
from PyQt5.QtCore import Qt, QSettings
import mysql.connector
from mysql.connector import Error
import bcrypt


# Custom widget for gradient background
class GradientWidget(QWidget):
    def __init__(self):
        super().__init__()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(1, QColor("#9C87E1"))
        gradient.setColorAt(0, QColor("#FCE3FD"))

        painter.fillRect(rect, QBrush(gradient))


class LoginWindow(GradientWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Group H", "MyApp")  # Replace with the actual name of the application
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 800, 600)

        # Create layout
        layout = QGridLayout()

        # Set the column stretches
        layout.setColumnStretch(0, 2)  # Picture area (2/3 of the width)
        layout.setColumnStretch(1, 1)  # Form area (1/3 of the width)

        # Add a picture
        picture_label = QLabel()
        pixmap = QPixmap("image 2 (1).png")
        picture_label.setPixmap(pixmap)
        picture_label.setScaledContents(True)
        layout.addWidget(picture_label, 1, 0, 6, 1)  # Spanning across 6 rows

        # Create a form layout for the inputs and buttons
        form_layout = QVBoxLayout()
        form_layout.setSpacing(0)  # Set the space between widgets in the form layout
        form_layout.setContentsMargins(100, 200, 100, 100)  # Set the margins of the form layout

        # Welcome and subwelcome label
        welcome_label = QLabel("Welcome")
        welcome_label.setStyleSheet("color: white; font-size: 88px; font-weight: bold; font-family: Baloo 2")
        form_layout.addWidget(welcome_label)

        subwelcome_label = QLabel("Please log in to your account.")
        subwelcome_label.setStyleSheet("color: #31376F; font-size: 20px; font-weight: bold")
        form_layout.addWidget(subwelcome_label)

        # Username label and input
        username_label = QLabel("Username:")
        username_label.setStyleSheet("color: white; font-size: 25px; font-weight: bold; font-family: Baloo 2")
        form_layout.addWidget(username_label)

        self.email_input = QLineEdit()
        self.email_input.setStyleSheet("background-color: white; border-radius: 15px; padding: 15px;")
        form_layout.addWidget(self.email_input)

        # Password label and input
        self.password_label = QLabel("Password:")
        self.password_label.setStyleSheet("color: white; font-size: 25px; font-weight: bold; font-family: Baloo 2")
        form_layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("background-color: white; border-radius: 15px; padding: 15px;")
        form_layout.addWidget(self.password_input)

        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setStyleSheet("color: white; font-family: Baloo 2; font-weight: bold")
        form_layout.addWidget(self.remember_checkbox)

        # Login button
        login_button = QPushButton("Login")
        login_button.setStyleSheet("background-color: #7976E8; color: white; border-radius: 15px; font-family: Baloo 2; font-weight: bold; height: 60px")
        login_button.clicked.connect(self.login)
        form_layout.addWidget(login_button)

        # Add the form layout to the grid layout
        layout.addLayout(form_layout, 0, 1, 6, 1)  # Spanning across 6 rows

        # Set layout
        self.setLayout(layout)

        # Load saved credentials if available
        self.load_credentials()

    def load_credentials(self):

        saved_email = self.settings.value("email", "")

        saved_password_hash = self.settings.value("password", "")

        if saved_email and saved_password_hash:
            self.email_input.setText(saved_email)

            self.password_input.setText(saved_password_hash)

            self.remember_checkbox.setChecked(True)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.critical(self, "Error", "Please enter the required information")
            return

        if "@" not in email:
            QMessageBox.critical(self, "Error", "Your email must contain the character '@'")
            return

        # Database connection
        try:
            connection = mysql.connector.connect(
                host='localhost',
                database='example',
                user='root',
                password='qwerty'  
            )

            if connection.is_connected():
                cursor = connection.cursor(dictionary=True)
                sql = "SELECT * FROM users WHERE email = %s"
                cursor.execute(sql, (email,))
                result = cursor.fetchone()

                if result:
                    userID = result['id']
                    name = result['name']
                    hashedPassword = result['password']

                    # Verify the entered password against the stored hashed password
                    if bcrypt.checkpw(password.encode(), hashedPassword.encode()):
                        if self.remember_checkbox.isChecked():
                            self.settings.setValue("email", email)
                            self.settings.setValue("password", password)
                        else:
                            self.settings.remove("email")
                            self.settings.remove("password")
                        # Simulate session and cookies
                        QMessageBox.information(self, "Login", f"Login Successful. Welcome {name}!")
                        self.close()
                        # Redirect to the next window or functionality
                    else:
                        QMessageBox.critical(self, "Error", "Wrong password")
                else:
                    QMessageBox.critical(self, "Error", "User not found")
        except Error as e:
            QMessageBox.critical(self, "Error", f"Error connecting to database: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load Baloo font
    try:
        font_id = QFontDatabase.addApplicationFont("Baloo2-VariableFont_wght.ttf")
        if font_id == -1:
            print("Failed to load font")
        else:
            baloo_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            print(f"Loaded font family: {baloo_font_family}")
            app.setFont(QFont(baloo_font_family))
    except Exception as e:
        print(f"Error loading font: {e}")

    # Load Quicksand font
    try:
        font_id_quicksand = QFontDatabase.addApplicationFont("Quicksand-VariableFont_wght.ttf")
        if font_id_quicksand == -1:
            print("Failed to load font")
        else:
            quicksand_font_family = QFontDatabase.applicationFontFamilies(font_id_quicksand)[0]
            print(f"Loaded font family: {quicksand_font_family}")
            app.setFont(QFont(quicksand_font_family))
    except Exception as e:
        print(f"Error loading font: {e}")

    login_window = LoginWindow()
    login_window.show()

    sys.exit(app.exec_())
