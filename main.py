import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["your_database_name"]  # Replace with your actual database name
collection = db["your_collection_name"]  # Replace with your collection name

app = FastAPI()

# Define Pydantic model for form validation
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running successfully with MongoDB Atlas!"}

@app.post("/submit")
def submit_form(form: ContactForm):
    try:
        form_data = form.dict()
        result = collection.insert_one(form_data)
        return {"message": "✅ Form submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to store data: {str(e)}")

@app.get("/submissions")
def get_submissions():
    try:
        submissions = []
        for submission in collection.find():
            submission["_id"] = str(submission["_id"])  # Convert ObjectId to string
            submissions.append(submission)
        return {"submissions": submissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to retrieve data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
