from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

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

            # Database connection details
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

    return render_template('ImportSQLFIle.html')

if __name__ == "__main__":
    app.run(debug=True)
