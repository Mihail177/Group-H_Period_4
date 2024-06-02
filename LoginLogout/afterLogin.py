# afterLogin.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class AfterLoginWindow(QWidget):
    def __init__(self, settings, login_window):
        super().__init__()
        self.settings = settings
        self.login_window = login_window
        self.initUI()

    def initUI(self):
        self.setWindowTitle("After Login")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        label = QLabel("You have successfully logged in!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px;")

        layout.addWidget(label)

        # Add a logout button
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet(
            "background-color: #FF6347; color: white; border-radius: 15px; font-family: Baloo 2; font-weight: bold; height: 60px")
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button)

        self.setLayout(layout)

    def logout(self):
        # Clear the saved credentials
        self.settings.remove("email")
        self.settings.remove("password")
        QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()
        self.login_window.show()
