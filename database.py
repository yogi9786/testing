from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGO_URI

client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

contact_db = client["contact_database"]
resume_db = client["resume_database"]
db = client["job_database"]

contact_collection = contact_db["contact_forms"]
resume_collection = resume_db["resumes"]
job_collection = db["job_data"]
