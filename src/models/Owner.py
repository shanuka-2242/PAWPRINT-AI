from pydantic import BaseModel

class Owner(BaseModel):
    NIC: str
    FullName: str
    Phone: str
    Email: str
    CurrentAddress: str
    Password: str