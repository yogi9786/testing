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
from typing import List


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["your_database_name"]
db = client["resume_db"]
collection = db["your_collection_name"]
collection = db["resumes"]

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
    phone: str
    email: str
    resume: str 


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
    
@app.post("/upload/")
async def upload_resume(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
):
    try:
        # Read file as binary and encode in Base64
        binary_data = await resume.read()
        encoded_resume = base64.b64encode(binary_data).decode("utf-8")
        
        # Store in MongoDB
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

@app.get("/resumes/", response_model=List[Resume])
def get_resumes():
    resumes = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB _id field
    return resumes

@app.get("/resume/{resume_id}")
def get_resume(resume_id: str):
    resume = collection.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume["_id"] = str(resume["_id"])
    return resume

@app.get("/download/{resume_id}")
def download_resume(resume_id: str):
    resume = collection.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Decode Base64 string back to binary
    binary_data = base64.b64decode(resume["resume"])
    
    # Save to a temporary PDF file
    file_path = f"temp_resume_{resume_id}.pdf"
    with open(file_path, "wb") as f:
        f.write(binary_data)

    # Return the file as a response
    return FileResponse(file_path, media_type="application/pdf", filename="resume.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
