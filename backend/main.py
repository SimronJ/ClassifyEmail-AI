from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from auth import router as auth_router
from gmail import router as gmail_router
from llm import router as llm_router
app.include_router(auth_router, prefix="/auth")
app.include_router(gmail_router, prefix="/gmail")
app.include_router(llm_router, prefix="/llm")

@app.get("/")
def root():
    return {"message": "ReadEmailAi Backend Running"} 