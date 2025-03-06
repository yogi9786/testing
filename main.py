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

# Defining different databases and collections
contact_db = client["contact_database"]
resume_db = client["resume_database"]

contact_collection = contact_db["contact_forms"]
resume_collection = resume_db["resumes"]

# Updating missing fields in the database
resume_collection.update_many({"phone": None}, {"$set": {"phone": ""}})
resume_collection.update_many({"resume": None}, {"$set": {"resume": ""}})

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
    phone: Optional[str] = None
    email: Optional[str] = None
    resume: Optional[str] = None


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

# Contact Form Submission API
@app.post("/submit")
def submit_contact_form(form: ContactForm):
    try:
        form_data = form.dict()
        result = contact_collection.insert_one(form_data)

        # Send email to the user
        send_email(form.email, form.name, form.message)

        return {"message": "Contact form submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        print("Error:", traceback.format_exc())  # Log detailed error
        raise HTTPException(status_code=500, detail="Internal Server Error. Check logs for details.")

# Get all contact form submissions
@app.get("/submissions", response_model=List[dict])
def get_contact_submissions():
    try:
        submissions = list(contact_collection.find({}, {"_id": 1, "name": 1, "email": 1, "message": 1}))

        return [
            {
                "id": str(sub["_id"]),
                "name": sub.get("name", "N/A"),
                "email": sub.get("email", "N/A"),
                "message": sub.get("message", "N/A"),
            }
            for sub in submissions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error. Check logs for details.")

# Delete a contact submission
@app.delete("/delete/{submission_id}")
def delete_contact_submission(submission_id: str = Path(..., title="Submission ID")):
    try:
        if not ObjectId.is_valid(submission_id):
            raise HTTPException(status_code=400, detail="Invalid submission ID format")
        
        result = contact_collection.delete_one({"_id": ObjectId(submission_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Submission not found")

        return {"message": "Submission deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete submission: {str(e)}")

# Resume Upload API
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
        result = resume_collection.insert_one(resume_data)
        return {"message": "Resume uploaded successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all resumes
@app.get("/resumes/")
def get_resumes():
    resumes = list(resume_collection.find({}, {"name": 1, "phone": 1, "email": 1, "resume": 1}))

    return [
        {
            "user_id": str(resume["_id"]),
            "name": resume.get("name", "N/A"),
            "phone": resume.get("phone", "N/A"),
            "email": resume.get("email", "N/A"),
            "resume_id": str(resume["_id"]),
        }
        for resume in resumes
    ]

# Get a specific resume
@app.get("/resume/{resume_id}")
def get_resume(resume_id: str):
    try:
        resume = resume_collection.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        resume["_id"] = str(resume["_id"])
        return resume
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Download Resume
@app.get("/download/{resume_id}")
def download_resume(resume_id: str):
    try:
        resume = resume_collection.find_one({"_id": ObjectId(resume_id)})
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
