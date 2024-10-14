import os
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing import image
from scipy.spatial.distance import cosine
import numpy as np
import csv
import sqlite3
from feature_extract import extract_features

# Load the pre-trained VGG16 model
model = VGG16(weights='imagenet', include_top=False)

users = [
    {
        "full_name": "John Doe",
        "NIC": "123456789V",
        "phone": "0771234567",
        "email": "john.doe@example.com",
        "current_address": "123 Main Street",
        "password": "password123",
        "image_file": "__c53XWoTJGgRsRS4MKOxAAAACMAARAD.jpg"  # Example image filename
    },
    # Add more users here...
]

db_path = os.path.join('Database', 'pawprint.db')
# load data 
train_data = r'D:\Text Books\NIBM\BSC\12.Individual Project\Dataset\archive\dog_nose_dataset\train\images'
# train_file = os.listdir(train_data)

# Connect to the SQLite database
conn = sqlite3.connect(db_path)

# Create a cursor object to interact with the database
cursor = conn.cursor()

# Create a table to store the data
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    NIC TEXT PRIMARY KEY,
                    full_name TEXT,
                    phone TEXT,
                    email TEXT,
                    current_address TEXT,
                    password TEXT,
                    feature_vector BLOB
                 )''')

# Iterate over users, extract features for each user's dog image, and save data in the database
for user in users:
    # Path to the user's dog image
    image_path = os.path.join(train_data, user['image_file'])

    # Extract feature vector from the dog's nose image
    features = extract_features(image_path)
    
    # Convert the feature vector to bytes (BLOB format)
    # feature_blob = features.tobytes()

    # Insert user information and feature vector into the SQLite database
    cursor.execute('''INSERT INTO users (NIC, full_name, phone, email, current_address, password, feature_vector)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (user['NIC'], user['full_name'], user['phone'], user['email'], user['current_address'], user['password'], features))

# Commit the changes to the database
conn.commit()

# Fetch and display the data stored in the database
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

for row in rows:
    print(f"NIC: {row[0]}, FullName: {row[1]}, Phone: {row[2]}, Email: {row[3]}, Current Address: {row[4]}")

# Close the database connection
conn.close()