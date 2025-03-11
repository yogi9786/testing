from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "FastAPI backend is running successfully with MongoDB Atlas!"}
