# main.py
import os
import re
import markdown
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from datetime import datetime

# Import all our utility functions
from utils.extract_text import extract_text_from_pdf
from utils.gemini_api import get_summary, get_analysis, get_wellness_score
from utils.simple_ats import calculate_ats_score

# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI application
app = FastAPI()

# Mount the 'static' directory to serve CSS, JS, and image files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup the Jinja2 templating engine to render HTML pages from the 'templates' directory
templates = Jinja2Templates(directory="templates")


# --- Route for the main upload page ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Renders the main upload page (upload.html).
    """
    return templates.TemplateResponse("upload.html", {"request": request})


# --- Route for handling the form submission and analysis ---
@app.post("/analyze", response_class=HTMLResponse)
async def analyze_resume(request: Request, resume: UploadFile = File(...), job_description: str = Form("")):
    """
    This endpoint processes the uploaded resume and optional job description.
    It calls the utility functions for text extraction and AI analysis,
    then renders the results on the result.html page.
    """
    # 1. Validate file type
    if resume.content_type != "application/pdf":
        return templates.TemplateResponse("upload.html", {"request": request, "error": "Invalid file type. Please upload a PDF."})
    
    # 2. Extract text from the PDF
    resume_text = await extract_text_from_pdf(resume)
    if not resume_text.strip():
        error_message = "Could not find any text to analyze. Please ensure your PDF is text-based and not an image or a scan."
        return templates.TemplateResponse("upload.html", {"request": request, "error": error_message})

    # 3. Perform AI Analysis (in sequence)
    # Get the current date to pass to the AI for accurate date evaluation
    current_date_str = datetime.now().strftime("%B %d, %Y")

    summary = await get_summary(resume_text)
    
    # Pass the current date to get_analysis as well
    detailed_analysis = await get_analysis(
        resume_text=resume_text, 
        current_date=current_date_str
    )
    
    # Pass the current date into the function call
    wellness_score_raw = await get_wellness_score(
        analysis_text=detailed_analysis, 
        current_date=current_date_str
    )

    # 4. Parse the Wellness Score and its explanation (UPDATED LOGIC)
    wellness_score_value = 0.0
    explanation_parts = []  # Use a list to build the full explanation string

    # Get the score
    score_match = re.search(r"Score:\s*([0-9.]+)", wellness_score_raw)
    if score_match:
        wellness_score_value = float(score_match.group(1))

    # Get the main explanation, stopping before an optional "Note:"
    explanation_match = re.search(r"Explanation:\s*(.*?)(?:\nNote:|$)", wellness_score_raw, re.DOTALL)
    if explanation_match:
        explanation_parts.append(explanation_match.group(1).strip())

    # Get the optional note, if it exists
    note_match = re.search(r"Note:\s*(.*)", wellness_score_raw, re.DOTALL)
    if note_match:
        explanation_parts.append(f"Note: {note_match.group(1).strip()}")

    # Combine the parts for the final display string
    wellness_score_explanation = "\n".join(explanation_parts) if explanation_parts else "Could not parse score."
    
    # Calculate percentage for the progress bar (Score / 10 * 100)
    wellness_score_percent = wellness_score_value * 10

    # 5. Convert Markdown results to HTML for safe rendering
    detailed_analysis_html = markdown.markdown(detailed_analysis)

    # 6. Handle ATS Scoring (only if a job description is provided)
    ats_score = 0
    ats_analysis_html = ""
    jd_provided = bool(job_description and job_description.strip())

    if jd_provided:
        ats_result = await calculate_ats_score(resume_text, job_description)
        ats_score = ats_result.get('score', 0)
        ats_analysis_html = markdown.markdown(ats_result.get('analysis', ''))

    # 7. Prepare all data to be sent to the template
    context = {
        "request": request,
        "summary": summary,
        "detailed_analysis_html": detailed_analysis_html,
        "wellness_score_value": wellness_score_value,
        "wellness_score_explanation": wellness_score_explanation,
        "wellness_score_percent": wellness_score_percent,
        "ats_score": ats_score,
        "ats_analysis_html": ats_analysis_html,
        "jd_provided": jd_provided
    }

    # 8. Render the final results page
    return templates.TemplateResponse("result.html", context)