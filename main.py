import os
import urllib.parse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"

client = AsyncIOMotorClient(MONGO_URI)
db = client["your_database_name"]  # Replace with your actual database name
collection = db["your_collection_name"]  # Replace with your collection name

app = FastAPI()

async def get_data():
    data = await collection.find_one()
    return data


# Define Pydantic model for form validation
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running successfully!"}

@app.post("/submit")
async def submit_form(form: ContactForm):
    try:
        form_data = form.dict()
        result = await collection.insert_one(form_data)
        return {"message": "Form submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store data: {str(e)}")

@app.get("/submissions")
async def get_submissions():
    try:
        submissions = []
        async for submission in collection.find():
            submissions.append(submission)
        return {"submissions": submissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
