import sqlite3
import base64

# Function to get an owner by NIC from the SQLite database
def get_owner_by_nic(nic: str):

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # SQL query to select the owner based on NIC
    cursor.execute('SELECT nic, full_name, phone, email, current_address, password FROM tb_owners WHERE nic = ?', (nic,))
    owner = cursor.fetchone()
    conn.close()

    # Return the owner if found, otherwise None
    if owner:
        return {
            'NIC': owner[0],
            'FullName': owner[1],
            'Phone': owner[2],
            'Email': owner[3],
            'CurrentAddress': owner[4],
            'Password': owner[5],
        }
    else:
        return None
    
# Function to get owners list from the SQLite database
def get_owners():

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # SQL query to select the owner based on NIC
    cursor.execute('SELECT * FROM tb_owners')
    owners_list = cursor.fetchall()
    conn.close()

    # Return the owner if found, otherwise None
    if owners_list:
        owners_data = []
        for owner in owners_list:
            owner_data = {
                'NIC': owner[0],
                'FullName': owner[1],
                'Phone': owner[2],
                'Email': owner[3],
                'CurrentAddress': owner[4],
                'Password': owner[5]
                }
            owners_data.append(owner_data)
        return owners_data
    else:
        return None
    
# Function to add owner into the SQLite database
def put_owner(nic:str, full_name:str, phone:str, email:str, current_address:str, password:str):

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # SQL query to insert registered dog into the SQLite database
    cursor.execute('INSERT INTO tb_owners (nic, full_name, phone, email, current_address, password) VALUES (?, ?, ?, ?, ?, ?)', (nic, full_name, phone, email, current_address, password))
    conn.commit()

    # Verification step: Retrieve the inserted record to confirm insertion
    cursor.execute('SELECT * FROM tb_owners WHERE nic = ?', (nic,))

     # Fetch the result of the query
    inserted_owner = cursor.fetchone()
    conn.close()

    # Return the owner if found, otherwise None
    if inserted_owner:
        return True
    else:
        return False 
    
# Function to get registred dogs list from the SQLite database
def get_registered_dogs():

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # SQL query to select the owner based on NIC
    cursor.execute('SELECT * FROM tb_registered_dogs')
    registered_dog_list = cursor.fetchall()
    conn.close()

    # Return the owner if found, otherwise None
    if registered_dog_list:
        return registered_dog_list
    else:
        return None

# Function to add registred dog into the SQLite database
def put_register_dog(dog_name:str, breed:str, age:str, feature_vector:bytes, owner_nic:str, dog_image:bytes):

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # SQL query to insert registered dog into the SQLite database
    cursor.execute('INSERT INTO tb_registered_dogs (dog_name, breed, age, feature_vector, owner_nic, dog_image) VALUES (?, ?, ?, ?, ?, ?)', (dog_name, breed, age, feature_vector, owner_nic, dog_image))
    conn.commit()

    # Verification step: Retrieve the inserted record to confirm insertion
    cursor.execute('SELECT * FROM tb_registered_dogs WHERE dog_name = ? AND owner_nic = ?', (dog_name, owner_nic))

     # Fetch the result of the query
    inserted_dog = cursor.fetchone()
    conn.close()

    # Return the owner if found, otherwise None
    if inserted_dog:
        return True
    else:
        return False 
    
# Function to get registred dog by entry ID & return dog info and owner info from the SQLite database
def get_registered_dog_and_owner(entry_id:str):

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # Verification step: Retrieve the inserted record to confirm insertion
    cursor.execute('SELECT * FROM tb_registered_dogs WHERE id = ?', (entry_id,))

     # Fetch the result of the query
    registered_dog_info = cursor.fetchone()
    conn.close()

    # Return the owner if found, otherwise None
    if registered_dog_info:
        owner_info = get_owner_by_nic(registered_dog_info[5])
        
        # Convert dog image to base 64 format
        dog_image_base64 = base64.b64encode(registered_dog_info[6]).decode('utf-8')
        if owner_info:
            verifiedData = {
                    'Dog':{
                        'EntryID': registered_dog_info[0],
                        'Name': registered_dog_info[1],
                        'Breed': registered_dog_info[2],
                        'Age': registered_dog_info[3],
                        'DogImage': dog_image_base64
                    },
                    'Owner':{
                        'NIC': owner_info['NIC'],
                        'FullName': owner_info['FullName'],
                        'Phone': owner_info['Phone'],
                        'Email': owner_info['Email'],
                        'CurrentAddress': owner_info['CurrentAddress']
                    }
                }
        return verifiedData
    else:
        return None 

#Function to remove registered dog from EntryID
def remove_dog_by_entry_id(entry_id: int):
    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()
    
    # Execute delete statement
    cursor.execute("DELETE FROM tb_registered_dogs WHERE id = ?;", (entry_id,))
    
    # Check if the deletion was successful
    rows_deleted = cursor.rowcount  # Gets number of rows affected by the delete statement
    conn.commit()  # Commit the transaction
    conn.close()   # Close the connection

    if rows_deleted > 0:
        return True  # Successfully deleted
    else:
        return False  # No row found to delete
        
# Function to get registered dog list by owner NIC from the SQLite database
def get_registered_dog_list_by_owner_nic(owner_nic: int):

    # Connect to the SQLite database
    conn = sqlite3.connect('Database/pawprint.db')
    cursor = conn.cursor()

    # SQL query to select the owner based on NIC
    cursor.execute('SELECT * FROM tb_registered_dogs WHERE owner_nic = ?', (owner_nic,))
    registered_dogs_list = cursor.fetchall()
    conn.close()

    # Return the dog if found, otherwise None
    if registered_dogs_list:
        registered_dogs_data = []
        for registered_dog in registered_dogs_list:

            #process each dog and convert image to Base64  
            dog_image_base64 = base64.b64encode(registered_dog[6]).decode('utf-8')
            registered_dog_data = {
                'EntryID': registered_dog[0],
                'Name': registered_dog[1],
                'Breed': registered_dog[2],
                'Age': registered_dog[3],
                'DogImage': dog_image_base64
                }
            registered_dogs_data.append(registered_dog_data)
        return registered_dogs_data
    else:
        return None