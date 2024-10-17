from fastapi import FastAPI,UploadFile,File,Form,HTTPException
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
from models.Owner import Owner 
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
        raise HTTPException(status_code=404, detail="Owners not found")

# Endpoint for get owner by NIC
@app.get('/registered_owners/{nic}', response_model=Owner)
async def registered_owner(nic: str):
    owner = get_owner_by_nic(nic)
    if owner:
        return owner
    else:
        raise HTTPException(status_code=404, detail="Owner not found")
    
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
        return owner
    else:
        raise HTTPException(status_code=404, detail="Owner not found")

# Endpoint for Register dog 
@app.post('/register-dog')
async def register_dog(file: UploadFile = File(...), 
                       dog_name:str = Form(...), 
                       breed:str = Form(...), 
                       age:str = Form(...), 
                       owner_nic: str = Form(...)):

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    # Create an empty dictionary to store the retrieved data
    retrieved_dataset = {}
    # Save the uploaded file
    image_file_path = os.path.join(temp_dir, file.filename)
    with open(image_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Fetch all the rows returned by the query
    registered_dogs_list = get_registered_dogs()

    # Iterate over the rows and populate the retrieved_dataset dictionary
    if not registered_dogs_list:
        owner_inputed_image_feature_array = extract_features(image_file_path)
        owner_inputed_image_feature_array_blob = sqlite3.Binary(owner_inputed_image_feature_array.tobytes())
        inserted_dog = put_register_dog(dog_name, breed, age, owner_inputed_image_feature_array_blob, owner_nic)
        if inserted_dog:
            return {"message": f"Dog '{dog_name}' registered successfully"}
        else:
            raise HTTPException(status_code=500, detail="Dog couldn't registered.")
    else:
        array_present = False

        for registered_dog in registered_dogs_list:
            entry_id = registered_dog[0]
            feature_array_buffer = registered_dog[4]
            feature_array = np.frombuffer(feature_array_buffer, dtype=np.float32)
            retrieved_dataset[entry_id] = feature_array
            
        print(len(list(retrieved_dataset.values())))
        owner_inputed_image_feature_array = extract_features(image_file_path)

        for feature_array in retrieved_dataset.values():
            if np.array_equal(feature_array, owner_inputed_image_feature_array):
                array_present = True
                break

        # If the array is not present, add it to the dataset
        if not array_present:
            # Convert the target_array to a binary representation
            owner_inputed_image_feature_array_blob = sqlite3.Binary(owner_inputed_image_feature_array.tobytes())
            inserted_dog = put_register_dog(dog_name, breed, age, owner_inputed_image_feature_array_blob, owner_nic)
            if inserted_dog:
                return {"message": f"Dog '{dog_name}' registered successfully"}
            else:
                 raise HTTPException(status_code=500, detail="Dog couldn't registered.")
        else:
            return f"'{dog_name}' is already registered."

@app.post('/verify-ownership')
async def verify_ownership(file: UploadFile = File(...)):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    # Save the uploaded file
    image_file_path = os.path.join(temp_dir, file.filename)

    with open(image_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    registered_dogs_list = get_registered_dogs()

    if registered_dogs_list:
        # Create an empty dictionary to store the retrieved data
        retrieved_dataset = {}

        # Iterate over the rows and populate the retrieved_dataset dictionary
        for registered_dog in registered_dogs_list:
            entry_id = registered_dog[5]
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

        return {'Most Similar Entry ID': max_similarity_entry_id}
    else:
        return f"No Dogs Registered Into The Paw Print Yet."
    
if __name__ == '__main__':
    uvicorn.run(app)