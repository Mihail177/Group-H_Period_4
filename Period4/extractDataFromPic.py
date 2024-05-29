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

# Load the image
image_path = 'cristi.jpg'
image = cv2.imread(image_path)

# Detect faces in the image
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
faces = detector(gray)

# Check if a face is detected
if len(faces) == 0:
    print("No face detected in the image.")
    exit()

# Process the first detected face
face = faces[0]
landmarks = predictor(gray, face)
face_descriptor = face_rec_model.compute_face_descriptor(image, landmarks)
np_face_descriptor = np.array(face_descriptor)

# Save the embedding with the user data
user_data = {
    'name': 'Cristi',
    'employee_id': '19',
    'face_descriptor': np_face_descriptor
}

# Save the user data to a file
with open('embeddings/cristi.pickle', 'wb') as f:
    pickle.dump(user_data, f)

print("Facial data extracted and saved.")
