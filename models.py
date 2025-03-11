from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

class Resume(BaseModel):
    id: Optional[str] = None 
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str
    applied_at: datetime.datetime
    resume: Optional[str] = None

class Location(BaseModel):
    city: str
    state: str
    country: str

class JobData(BaseModel):
    role: str
    description: str
    location: Location
