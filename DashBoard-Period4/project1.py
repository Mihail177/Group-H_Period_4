import sys
from PyQt5.QtCore import QUrl  # Import QUrl class
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFontDatabase, QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browse")
        self.setGeometry(100, 100, 800, 600)

        # Load the custom fonts
        font1_id = QFontDatabase.addApplicationFont(r"C:\Users\PC\PycharmProjects\pythonProject\Group-H_Period_4\DashBoard-Period4\CSS\Baloo2-Bold.ttf")
        font2_id = QFontDatabase.addApplicationFont(r"C:\Users\PC\PycharmProjects\pythonProject\Group-H_Period_4\DashBoard-Period4\CSS\Quicksand-VariableFont_wght.ttf")

        if font1_id != -1:
            font1_families = QFontDatabase.applicationFontFamilies(font1_id)
            if font1_families:
                font1 = QFont(font1_families[0])
                print(f"Font1 loaded: {font1_families[0]}")
            else:
                print("No font families found for Font1.")
        else:
            print("Font1 could not be loaded.")

        if font2_id != -1:
            font2_families = QFontDatabase.applicationFontFamilies(font2_id)
            if font2_families:
                font2 = QFont(font2_families[0])
                print(f"Font2 loaded: {font2_families[0]}")
            else:
                print("No font families found for Font2.")
        else:
            print("Font2 could not be loaded.")

        # Create a QWebEngineView
        self.web_view = QWebEngineView()

        # Load the local HTML file
        self.web_view.setUrl(QUrl.fromLocalFile(r"C:\Users\PC\PycharmProjects\pythonProject\Group-H_Period_4\DashBoard-Period4\DashBoard.html"))

        # Set the central widget
        self.setCentralWidget(self.web_view)

        self.resizeEvent = self.on_resize

    def on_resize(self, event):
        # Get the current window size
        width = self.size().width()
        height = self.size().height()

        # Adjust zoom factor based on the window size
        # Here, 800x600 is considered as the base size for zoom factor 1.0
        base_width = 800
        base_height = 600
        width_ratio = width / base_width
        height_ratio = height / base_height
        zoom_factor = min(width_ratio, height_ratio)

        self.web_view.setZoomFactor(zoom_factor)
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
