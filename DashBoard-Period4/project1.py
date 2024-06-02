import sys
import threading
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFontDatabase, QFont
from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
import os

# Flask application setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to import SQL file into the database
def import_sql_file(connection, sql_file_path):
    cursor = connection.cursor()
    with open(sql_file_path, 'r') as file:
        sql = file.read()

    commands = sql.split(';')
    for command in commands:
        if command.strip():
            try:
                cursor.execute(command)
                connection.commit()
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                connection.rollback()
    cursor.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            config = {
                'user': 'yenphan',
                'password': 'Yen17082003@',
                'host': 'localhost',
                'database': 'importFile',
                'raise_on_warnings': True
            }

            try:
                connection = mysql.connector.connect(**config)
                import_sql_file(connection, file_path)
                connection.close()
                return 'SQL file imported successfully'
            except mysql.connector.Error as err:
                return f"Error: {err}"

    return render_template(r'C:\Users\PC\PycharmProjects\pythonProject\Group-H_Period_4\DashBoard-Period4\ImportSQLFIle.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Example validation
        if username == 'admin' and password == 'password':
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials'
    return render_template(r'C:\Users\PC\PycharmProjects\pythonProject\Group-H_Period_4\DashBoard-Period4\LoginLogout\login.py')

# PyQt5 application setup
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
        width = self.size().width()
        height = self.size().height()
        base_width = 800
        base_height = 600
        width_ratio = width / base_width
        height_ratio = height / base_height
        zoom_factor = min(width_ratio, height_ratio)
        self.web_view.setZoomFactor(zoom_factor)
        super().resizeEvent(event)

def run_flask():
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    qt_app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(qt_app.exec_())
