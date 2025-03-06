import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import traceback
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["your_database_name"]
collection = db["your_collection_name"]

# SendGrid API Key
if os.getenv("SENDGRID_API_KEY"):
    print("SENDGRID_API_KEY loaded successfully!")
else:
    print("SENDGRID_API_KEY is missing!")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = "yogesh.v@xtransmatrix.com" 

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
