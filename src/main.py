from fastapi import FastAPI,UploadFile,File,Form,HTTPException,Response
import uvicorn
import shutil
import tempfile
from scipy.spatial.distance import cosine
import sqlite3
import numpy as np
from extract_features import extract_features
from common_functions import get_owner_by_nic
from common_functions import get_owners
from common_functions import put_owner
from common_functions import get_registered_dogs
from common_functions import put_register_dog
from common_functions import get_registered_dog_and_owner
from common_functions import get_registered_dog_list_by_owner_nic
from common_functions import remove_dog_by_entry_id
import os


app = FastAPI()


# Main endpoint
@app.get('/')
async def welcome():
    return 'Welcome To PAWPRINT-AI Backend'


# Endpoint for get signedin owners list
@app.get('/registered_owners')
async def registered_owners():
    owners_list = get_owners()
    if owners_list:
        return owners_list
    else:
        raise HTTPException(status_code=404)


# Endpoint for get owner by NIC
@app.get('/registered_owners/{nic}')
async def registered_owner(nic: str):
    owner = get_owner_by_nic(nic)
    if owner:
        return owner
    else:
        raise HTTPException(status_code=404)
    

# Endpoint for register owner
@app.post('/register_owner')
async def register_owner(nic:str = Form(...), 
                        full_name:str = Form(...), 
                        phone:str = Form(...), 
                        email: str = Form(...),
                        current_address: str = Form(...),
                        password: str = Form(...)):
    owner = put_owner(nic, full_name, phone, email, current_address, password)
    if owner:
        return Response(status_code=200)
    else:
        raise HTTPException(status_code=404)


# Endpoint for Register dog 
@app.post('/register_dog')
async def register_dog(nose_image: UploadFile = File(...), 
                       dog_image: UploadFile = File(...), 
                       dog_name:str = Form(...), 
                       breed:str = Form(...), 
                       age:str = Form(...), 
                       owner_nic: str = Form(...)):
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create an empty dictionary to store the retrieved data
    retrieved_dataset = {}

    # File path to save the uploaded files in the temp folders
    nose_image_file_path = os.path.join(temp_dir, nose_image.filename)
    dog_image_file_path = os.path.join(temp_dir, dog_image.filename)

    # Save dog nose image into temp folder path
    with open(nose_image_file_path, 'wb') as f:
        shutil.copyfileobj(nose_image.file, f)

    # Save dog image into temp folder path
    with open(dog_image_file_path, 'wb') as f:
        shutil.copyfileobj(dog_image.file, f)

    # Fetch all the registered dogs
    registered_dogs_list = get_registered_dogs()

    # If the fetched registered dog is empty save the dog into the database
    if not registered_dogs_list:

        # Read the dog image as bytes to store in the database
        with open(dog_image_file_path, 'rb') as f:
            dog_image_as_bytes = f.read()

        # Extract feature from the image and convert feature array into BLOB format to save in the database
        owner_inputed_image_feature_array = extract_features(nose_image_file_path)
        owner_inputed_image_feature_array_blob = sqlite3.Binary(owner_inputed_image_feature_array.tobytes())

        #Insert the registered dog into the database
        inserted_dog = put_register_dog(dog_name, breed, age, owner_inputed_image_feature_array_blob, owner_nic, dog_image_as_bytes)

        if inserted_dog:
            return Response(status_code=200)
        else:
            raise HTTPException(status_code=500)
    
    # If the fetched registered dog is not empty
    else:

        # Maintaining Bool to check if feature array is already present
        array_present = False

        # Iterate trough fetched registered dog list and populate dictionary
        for registered_dog in registered_dogs_list:
            entry_id = registered_dog[0]
            feature_array_buffer = registered_dog[4]
            feature_array = np.frombuffer(feature_array_buffer, dtype=np.float32)
            retrieved_dataset[entry_id] = feature_array

        # Extract feature from the image 
        owner_inputed_image_feature_array = extract_features(nose_image_file_path)

        # Check if array is alrady in the database
        for feature_array in retrieved_dataset.values():
            if np.array_equal(feature_array, owner_inputed_image_feature_array):
                array_present = True
                break

        # If the array is not present, add it to the dataset
        if not array_present:

            # Convert the target_array to a binary representation
            owner_inputed_image_feature_array_blob = sqlite3.Binary(owner_inputed_image_feature_array.tobytes())

            # Read the dog image as bytes to store in the database
            with open(dog_image_file_path, 'rb') as f:
                dog_image_as_bytes = f.read()

            # Insert dog into the database
            inserted_dog = put_register_dog(dog_name, breed, age, owner_inputed_image_feature_array_blob, owner_nic, dog_image_as_bytes)

            # Check if inserted dog is true of false and return status code
            if inserted_dog:
                return Response(status_code=200)
            else:
                 raise HTTPException(status_code=500)
        else:
            return Response(status_code=400)


# Endpoint for verify ownership 
@app.post('/verify_ownership')
async def verify_ownership(file: UploadFile = File(...)):

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Tempory file path to save the uploaded nose image
    image_file_path = os.path.join(temp_dir, file.filename)

    # Save the image
    with open(image_file_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)

    # Fetch registered dog list
    registered_dogs_list = get_registered_dogs()

    # If registered dog list not empty 
    if registered_dogs_list:

        # Create an empty dictionary to store the retrieved data
        retrieved_dataset = {}

        # Iterate over the rows and populate the retrieved_dataset dictionary
        for registered_dog in registered_dogs_list:
            entry_id = registered_dog[0]
            feature_array_buffer = registered_dog[4]
            feature_array = np.frombuffer(feature_array_buffer, dtype=np.float32)
            retrieved_dataset[entry_id] = feature_array

        # Extract features from the new image
        user_inputed_image_features = extract_features(image_file_path)

        # Compare the new image features with the dataset using cosine similarity
        max_similarity = -1
        max_similarity_entry_id = None

        for entry_id, existing_img_features in retrieved_dataset.items():
            similarity = 1 - cosine(existing_img_features, user_inputed_image_features)
            if similarity > max_similarity:
                max_similarity = similarity
                max_similarity_entry_id = entry_id

        # Convert number to one decimal number
        truncated_number = float(str(max_similarity)[:3])

        if truncated_number > 0.8:

            results = get_registered_dog_and_owner(max_similarity_entry_id)
            
            if results:
                return results
            else:
                return HTTPException(status_code=404)
                
        else:
            return HTTPException(status_code=404)
        
    else:
        return HTTPException(status_code=404)


# Endpoint to get registered dog info by owner NIC
@app.get("/registered_dog/{owner_nic}")
async def get_dog_info_by_owner_nic(owner_nic: int):
    
    # Fetch image data from the database
    dog_data = get_registered_dog_list_by_owner_nic(owner_nic)
    
    if dog_data:
        return dog_data
    else:
        raise HTTPException(status_code=404)


# Endpoint to remove registered dog info by EntryID
@app.delete("/registered_dog/{entry_id}")
async def remove_registered_dog_by_entry_id(entry_id: int):
    
    # Remove registered dog from the database
    dog_data = remove_dog_by_entry_id(entry_id)
    
    if dog_data:
        return Response(status_code=200)
    else:
        raise HTTPException(status_code=404)
    

if __name__ == '__main__':
    uvicorn.run(app)