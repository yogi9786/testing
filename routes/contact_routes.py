from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse
from database import contact_collection
from models import ContactForm
from services.email_service import send_email
import pandas as pd
import openpyxl
from bson import ObjectId

router = APIRouter()

@router.post("/submit")
def submit_contact_form(form: ContactForm):
    form_data = form.dict()
    result = contact_collection.insert_one(form_data)

    email_content = f"""
    <html>
        <body>
            <h2>Hello {form.name},</h2>
            <p>Thank you for reaching out to us!</p>
            <p>Your message: {form.message}</p>
            <br>
            <p>Best Regards,<br>XTRANSMATRIX CONSULTING SERVICES PVT LTD</p>
        </body>
    </html>
    """

    send_email(form.email, "Thank you for contacting us!", email_content)
    return {"message": "Contact form submitted successfully", "id": str(result.inserted_id)}

@router.get("/submissions")
def get_contact_submissions():
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

@router.get("/contacts-excel")
def export_contacts_to_excel():
    contacts = list(contact_collection.find({}, {"_id": 0}))

    if not contacts:
        raise HTTPException(status_code=404, detail="No contact data found to export.")

    df = pd.DataFrame(contacts)
    file_path = "contact_data.xlsx"
    df.to_excel(file_path, index=False, engine="openpyxl")

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="contact_data.xlsx"
    )

@router.delete("/delete/{submission_id}")
def delete_contact_submission(submission_id: str = Path(..., title="Submission ID")):
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID format")

    result = contact_collection.delete_one({"_id": ObjectId(submission_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {"message": "Submission deleted successfully"}