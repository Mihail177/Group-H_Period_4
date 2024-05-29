import cv2
import dlib
import numpy as np
import pickle
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker

# Paths to the model files
predictor_path = 'shape_predictor_68_face_landmarks.dat'
face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'

# Initialize the face detector, shape predictor, and face recognition model
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)
face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)

# Database credentials
server = 'facesystemlock.database.windows.net'
database = 'facesystemlock'
username = 'superadmin'
password = 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'

# Connection string
connection_string = f'mssql+pymssql://{username}:{password}@{server}:1433/{database}'

# Create SQLAlchemy engine
engine = create_engine(connection_string)

# Define metadata
metadata = MetaData()

# Reflect the employee table
employee_table = Table('employeez', metadata, autoload_with=engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Retrieve all rows from the employeez table
employees = session.query(employee_table).all()

# Close the session
session.close()

# Prepare known face descriptors
known_face_descriptors = []
known_names = []

for employee in employees:
    face_descriptor_blob = employee.facial_data
    face_descriptor = np.frombuffer(face_descriptor_blob, dtype=np.float64)  # Adjust this line based on how your data is stored
    known_face_descriptors.append(face_descriptor)
    known_names.append(employee.name)

# Open a connection to the webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)
        face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)
        np_face_descriptor = np.array(face_descriptor)

        # Compare with known face descriptors
        min_distance = float('inf')
        matched_name = "Unknown"

        for i, known_face_descriptor in enumerate(known_face_descriptors):
            distance = np.linalg.norm(known_face_descriptor - np_face_descriptor)
            if distance < min_distance:
                min_distance = distance
                matched_name = known_names[i]

        # Set a threshold for considering a face as recognized (e.g., 0.6)
        if min_distance < 0.6:
            name = matched_name
            print(f"Face matches with distance {min_distance:.2f}. You now have access to the room, {name}.")
        else:
            name = "Unknown"
            print("Face does not match. Access denied.")

        # Draw a rectangle around the face and label it
        x, y, w, h = (face.left(), face.top(), face.width(), face.height())
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow('Facial Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
