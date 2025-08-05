import os
import re
import markdown
from datetime import datetime

from fastapi import FastAPI, Request, Form, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import all our new and existing modules
from db import models, schemas
from db.database import engine, SessionLocal
from auth import hashing, jwt_handler
from utils.extract_text import extract_text_from_pdf
from utils.gemini_api import get_summary, get_analysis, get_wellness_score
from utils.simple_ats import calculate_ats_score

# --- Initial Setup ---

# Create the database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

load_dotenv()
app = FastAPI()

# Mount static files and setup templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Database Dependency ---
def get_db():
    """Dependency to get a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Authentication Endpoints ---

@app.post("/signup", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Endpoint for new user registration."""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered")
    
    hashed_pwd = hashing.hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint for user login, returns a JWT."""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not hashing.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = jwt_handler.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Application Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the main upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_resume(
    request: Request,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(jwt_handler.get_current_user), # PROTECTS THIS ROUTE
    resume: UploadFile = File(...),
    job_description: str = Form("")
):
    """
    Protected endpoint to analyze a resume for the currently logged-in user.
    """
    # 1. & 2. Validation and Text Extraction (unchanged)
    if resume.content_type != "application/pdf":
        return templates.TemplateResponse("upload.html", {"request": request, "error": "Invalid file type."})
    
    resume_text = await extract_text_from_pdf(resume)
    if not resume_text.strip():
        return templates.TemplateResponse("upload.html", {"request": request, "error": "Could not extract text."})

    # 3. Perform AI Analysis (unchanged)
    current_date_str = datetime.now().strftime("%B %d, %Y")
    summary = await get_summary(resume_text)
    detailed_analysis = await get_analysis(resume_text=resume_text, current_date=current_date_str)
    wellness_score_raw = await get_wellness_score(analysis_text=detailed_analysis, current_date=current_date_str)

    # 4. Parsing and data prep (unchanged)
    wellness_score_value = 0.0
    explanation_parts = []
    score_match = re.search(r"Score:\s*([0-9.]+)", wellness_score_raw)
    if score_match:
        wellness_score_value = float(score_match.group(1))
    explanation_match = re.search(r"Explanation:\s*(.*?)(?:\nNote:|$)", wellness_score_raw, re.DOTALL)
    if explanation_match:
        explanation_parts.append(explanation_match.group(1).strip())
    note_match = re.search(r"Note:\s*(.*)", wellness_score_raw, re.DOTALL)
    if note_match:
        explanation_parts.append(f"Note: {note_match.group(1).strip()}")
    wellness_score_explanation = "\n".join(explanation_parts) if explanation_parts else "Could not parse score."
    wellness_score_percent = wellness_score_value * 10
    detailed_analysis_html = markdown.markdown(detailed_analysis)
    
    # ... rest of the logic is the same ...
    ats_score = 0
    ats_analysis_html = ""
    jd_provided = bool(job_description and job_description.strip())
    if jd_provided:
        ats_result = await calculate_ats_score(resume_text, job_description)
        ats_score = ats_result.get('score', 0)
        ats_analysis_html = markdown.markdown(ats_result.get('analysis', ''))
    
    context = { "request": request, "summary": summary, "detailed_analysis_html": detailed_analysis_html, "wellness_score_value": wellness_score_value, "wellness_score_explanation": wellness_score_explanation, "wellness_score_percent": wellness_score_percent, "ats_score": ats_score, "ats_analysis_html": ats_analysis_html, "jd_provided": jd_provided }

    return templates.TemplateResponse("result.html", context)