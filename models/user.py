from pydantic import BaseModel

class user(BaseModel):
    full_name: str
    NIC: str
    phone: str
    email: str
    current_address: str
    password: str