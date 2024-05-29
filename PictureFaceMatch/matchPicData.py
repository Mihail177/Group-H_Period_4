import cv2
import dlib
import numpy as np
import pickle

# Paths to the model files
predictor_path = 'shape_predictor_68_face_landmarks.dat'
face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'

# Initialize the face detector, shape predictor, and face recognition model
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)
face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)

# Load the stored embedding
with open('embeddings/joris.pickle', 'rb') as f:
    user_data = pickle.load(f)
known_face_descriptor = user_data['face_descriptor']
known_name = user_data['name']

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

        # Calculate the Euclidean distance between the known face and the detected face
        distance = np.linalg.norm(known_face_descriptor - np_face_descriptor)
        print(f"Distance: {distance}")

        # Set a threshold for considering a face as recognized (e.g., 0.6)
        if distance < 0.6:
            name = known_name
            print(f"Face matches. You now have access to the room, {name}.")
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
