# -*- coding: utf-8 -*-

# Import necessary libraries
import zipfile
import os
import tensorflow as tf
from tensorflow.keras import models, layers
from tensorflow.keras.datasets import fashion_mnist
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, jsonify
from PIL import Image

# Unzipping file
with zipfile.ZipFile('/content/archive (2).zip', 'r') as zip_ref:
    zip_ref.extractall('fashion_data')  # Extract into a folder named 'fashion_data'

# Load Fashion MNIST dataset
(train_images, train_labels), (test_images, test_labels) = fashion_mnist.load_data()

# Normalize pixel values to be between 0 and 1
train_images = train_images / 255.0
test_images = test_images / 255.0

# Reshape data to include the color channel dimension (grayscale images have 1 channel)
train_images = train_images[..., np.newaxis]
test_images = test_images[..., np.newaxis]

# Define the CNN model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')  # 10 classes for Fashion MNIST
])

# Compile the model
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Train the model
history = model.fit(train_images, train_labels, epochs=10, validation_split=0.2, verbose=2)

# Evaluate the model on the test dataset
test_loss, test_acc = model.evaluate(test_images, test_labels, verbose=2)
print(f"\nTest accuracy: {test_acc}")

# Save the model in native Keras format
model.save('fashion_mnist_model.keras')

# Flask API Setup
app = Flask(__name__)

# Load your trained Fashion MNIST model
model_path = 'fashion_mnist_model.keras'
if not os.path.isfile(model_path):
    raise FileNotFoundError(f"Model file '{model_path}' not found.")
model = tf.keras.models.load_model(model_path)
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Fashion MNIST class names
class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

def normalize_image(image_path):
    try:
        # Load and preprocess the image
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        img = img.resize((28, 28))  # Resize to 28x28
        img_array = np.array(img)
        img_array = img_array / 255.0  # Rescale pixel values to [0, 1]
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        img_array = np.expand_dims(img_array, axis=-1)  # Add channel dimension
        return img_array
    except Exception as e:
        print(f"Error in normalize_image: {str(e)}")
        return None

@app.route('/')
def index():
    return "Simple API to classify Fashion MNIST images, with Flask!"

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    try:
        # Initialize an empty list to store predictions
        predictions = []

        # Directory path containing multiple images
        image_dir = 'new_data'  # Ensure the correct directory path is set
        image_paths = [os.path.join(image_dir, filename) for filename in os.listdir(image_dir) if filename.endswith('.jpg')]

        # Check if there are no images to process
        if not image_paths:
            return jsonify({'message': 'No new data to process'})

        # Process each image in the batch
        for image_path in image_paths:
            normalized_image = normalize_image(image_path)

            if normalized_image is not None:
                # Make predictions using your model
                prediction = model.predict(normalized_image)
                print(f"Raw predictions for {image_path}: {prediction}")

                # Interpret the result and append it to the predictions list
                predicted_class = class_names[np.argmax(prediction)]
                predictions.append({'image': image_path, 'prediction': predicted_class})
            else:
                print(f"Image normalization failed for {image_path}")

        return jsonify({'predictions': predictions})

    except Exception as e:
        print(f"Error in /predict endpoint: {str(e)}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
