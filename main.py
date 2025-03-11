from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import contact_routes, resume_routes, job_routes, common_routes
from middleware import IgnoreFaviconMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(IgnoreFaviconMiddleware)

app.include_router(common_routes.router)
app.include_router(contact_routes.router)
app.include_router(resume_routes.router)
app.include_router(job_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
