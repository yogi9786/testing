from fastapi import APIRouter, HTTPException
from database import job_collection
from models import JobData
from bson import ObjectId

router = APIRouter()

@router.post("/jobsend/")
def create_job_data(job_data: JobData):
    data = job_data.dict()
    result = job_collection.insert_one(data)
    return {"message": "Job data created successfully", "id": str(result.inserted_id)}

@router.get("/jobs/")
def get_jobs():
    jobs = list(job_collection.find())
    return [
        {
            "id": str(job["_id"]),
            "role": job["role"],
            "description": job["description"],
            "location": job["location"]
        }
        for job in jobs
    ]

@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = job_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": str(job["_id"]),
        "role": job["role"],
        "description": job["description"],
        "location": job["location"]
    }

@router.put("/jobs/{job_id}")
def update_job(job_id: str, updated_data: JobData):
    result = job_collection.update_one({"_id": ObjectId(job_id)}, {"$set": updated_data.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job data updated successfully"}

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    result = job_collection.delete_one({"_id": ObjectId(job_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job data deleted successfully"}
