import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QCheckBox
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPixmap, QFontDatabase, QFont, QBrush, QCursor
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
import pymssql
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

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class RegistrationWindow(GradientWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Group H", "MyApp")
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
        form_layout.setSpacing(0)
        form_layout.setContentsMargins(100, 200, 100, 100)

        # Welcome and subwelcome label
        welcome_label = QLabel("Sign up")
        welcome_label.setStyleSheet("color: white; font-size: 90px; font-weight: bold; font-family: Berkshire Swash")
        form_layout.addWidget(welcome_label)

        subwelcome_label = QLabel("Please fill in your email and password")
        subwelcome_label.setStyleSheet("color: #31376F; font-size: 20px; font-weight: bold; font-family: Quicksand")
        form_layout.addWidget(subwelcome_label)

        # Username label and input
        username_label = QLabel("Username:")
        username_label.setStyleSheet("color: white; font-size: 25px; font-weight: bold; font-family: Baloo 2")
        form_layout.addWidget(username_label)

        self.email_input = QLineEdit()
        self.email_input.setStyleSheet("background-color: white; border-radius: 15px; padding: 15px; font-family: Quicksand")
        form_layout.addWidget(self.email_input)

        # Password label and input
        self.password_label = QLabel("Password:")
        self.password_label.setStyleSheet("color: white; font-size: 25px; font-weight: bold; font-family: Baloo 2")
        form_layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("background-color: white; border-radius: 15px; padding: 15px")
        form_layout.addWidget(self.password_input)

        # Login button
        login_button = QPushButton("Register")
        login_button.setStyleSheet(
            "background-color: #7976E8; color: white; border-radius: 15px; font-family: Berkshire Swash; font-weight: bold; height: 60px; margin-top: 20px")
        login_button.clicked.connect(self.register)
        form_layout.addWidget(login_button)

        # Add the form layout to the grid layout
        layout.addLayout(form_layout, 0, 1, 6, 1)

        # Set layout
        self.setLayout(layout)

    def register(self):
        email = self.email_input.text()
        password = self.password_input.text()

        errors = []
        if not email or not password:
            errors.append("Please fill in the required information")
        if "@" not in email:
            errors.append("Your email must contain the character @")

        if errors:
            QMessageBox.critical(self, "Error", "\n".join(errors))
            return

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            connection = pymssql.connect(
                server='facesystemlock.database.windows.net',
                user='superadmin',
                password='LKWW8mLOO&amp;qzV0La4NqYzsGmF',
                database='facesystemlock',
            )

            cursor = connection.cursor(as_dict=True)
            sql = "INSERT INTO dbo.ADMIN (email_address, password) VALUES (%s, %s)"
            cursor.execute(sql, (email, hashed_password))
            connection.commit()
            cursor.close()
            connection.close()

            QMessageBox.information(self, "Success", "Registration successful!")
            self.close()
        except pymssql.DatabaseError as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load Berkshire font
    try:
        font_id = QFontDatabase.addApplicationFont("BerkshireSwash-Regular.ttf")
        if font_id == -1:
            print("Failed to load font")
        else:
            berkshire_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            print(f"Loaded font family: {berkshire_font_family}")
            app.setFont(QFont(berkshire_font_family))
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

    regis_window = RegistrationWindow()
    regis_window.show()
    sys.exit(app.exec_())
