from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


MONGO_URI = os.getenv("mongodb://localhost:27017")  
client = AsyncIOMotorClient(MONGO_URI)
db = client["contact_db"]
collection = db["submissions"]

# Define Pydantic model for form validation
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    
    
@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running successfully!"}

# API endpoint to store form data
@app.post("/submit")
async def submit_form(form: ContactForm):
    try:
        form_data = form.dict()
        result = await collection.insert_one(form_data)
        return {"message": " Form submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f" Failed to store data: {str(e)}")

# API endpoint to retrieve all form submissions
@app.get("/submissions")
async def get_submissions():
    try:
        submissions = []
        async for submission in collection.find():
            submissions.append(submission)
        return {"submissions": submissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f" Failed to retrieve data: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)