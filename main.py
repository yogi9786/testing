import os
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, EmailStr
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import traceback
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi.responses import FileResponse
import base64
from bson import ObjectId
from typing import List, Optional
from fastapi.params import Path


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["your_database_name1"]
db = client["resume1_db"]
collection = db["your_collection_name1"]
collection = db["resumes1"]

# Update documents where phone or resume is None
collection.update_many({"phone": None}, {"$set": {"phone": ""}})
collection.update_many({"resume": None}, {"$set": {"resume": ""}})

if os.getenv("SENDGRID_API_KEY"):
    print("SENDGRID_API_KEY loaded successfully!")
else:
    print("SENDGRID_API_KEY is missing!")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    
class Resume(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None  # Change from EmailStr to str to avoid validation errors
    resume: str | None = None


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running successfully with MongoDB Atlas!"}

def send_email(to_email: str, name: str, message: str):
    """Function to send email using SendGrid."""
    try:
        email_content = f"""
        <html>
            <body>
                <h2>Hello {name},</h2>
                <p>Thank you for reaching out to us!</p>
                <p>Your message: {message}</p>
                <p>We will get back to you soon.</p>
                <br>
                <p>Best Regards,<br>XTRANSMATRIX CONSULTING SERVICES PVT LTD</p>
            </body>
        </html>
        """

        mail = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject="Thank you for contacting us!",
            html_content=email_content
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mail)
        return response.status_code
    except Exception as e:
        print("SendGrid Error:", traceback.format_exc())

@app.post("/submit")
def submit_form(form: ContactForm):
    try:
        form_data = form.dict()
        result = collection.insert_one(form_data)

        # Send email to the user
        send_email(form.email, form.name, form.message)

        return {"message": "Form submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        print("Error:", traceback.format_exc())  # Log detailed error
        raise HTTPException(status_code=500, detail="Internal Server Error. Check logs for details.")

@app.get("/submissions")
def get_submissions():
    try:
        submissions = []
        for submission in collection.find():
            submission["_id"] = str(submission["_id"])
            submissions.append(submission)
        return {"submissions": submissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")
    
@app.delete("/delete/{submission_id}")
def delete_submission(submission_id: str = Path(..., title="Submission ID")):
    try:
        if not ObjectId.is_valid(submission_id):
            raise HTTPException(status_code=400, detail="Invalid submission ID format")
        
        result = collection.delete_one({"_id": ObjectId(submission_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Submission not found")

        return {"message": "Submission deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete submission: {str(e)}")
    
@app.post("/upload/")
async def upload_resume(
    name: str = Form(...),
    phone: str = Form(...),
    email: EmailStr = Form(...),
    resume: UploadFile = File(...),
):
    try:
        binary_data = await resume.read()
        encoded_resume = base64.b64encode(binary_data).decode("utf-8")
        resume_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "resume": encoded_resume,
        }
        result = collection.insert_one(resume_data)
        return {"message": "Resume uploaded successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resumes/")
def get_resumes():
    resumes = collection.find({}, {"name": 1, "phone": 1, "email": 1, "resume": 1})
    return [
        {
            "user_id": str(resume["_id"]),  # Add this field to frontend
            "name": resume["name"],
            "phone": resume["phone"],
            "email": resume["email"],
            "resume_id": str(resume["_id"]),
        }
        for resume in resumes
    ]  



@app.get("/resume/{resume_id}")
def get_resume(resume_id: str):
    try:
        resume = collection.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume["_id"] = str(resume["_id"])
        return resume
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{resume_id}")
def download_resume(resume_id: str):
    try:
        resume = collection.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        binary_data = base64.b64decode(resume["resume"])
        file_path = f"temp_resume_{resume_id}.pdf"
        with open(file_path, "wb") as f:
            f.write(binary_data)

        return FileResponse(file_path, media_type="application/pdf", filename="resume.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
