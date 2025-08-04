import os
import re
import markdown
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import all our utility functions
from utils.extract_text import extract_text_from_pdf
from utils.gemini_api import get_summary, get_analysis, get_wellness_score
from utils.simple_ats import calculate_ats_score

# Load environment variables from the .env file
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
    if not resume_text:
        return templates.TemplateResponse("upload.html", {"request": request, "error": "Could not extract text from the PDF. The file might be empty or corrupted."})

    # 3. Perform AI Analysis (in sequence)
    summary = await get_summary(resume_text)
    detailed_analysis = await get_analysis(resume_text)
    # The wellness score is based on the detailed analysis
    wellness_score_raw = await get_wellness_score(analysis_text=detailed_analysis)

    # 4. Parse the Wellness Score and its explanation
    wellness_score_value = 0.0
    wellness_score_explanation = "Could not parse score."
    score_match = re.search(r"Score:\s*([0-9.]+)", wellness_score_raw)
    if score_match:
        wellness_score_value = float(score_match.group(1))
    explanation_match = re.search(r"Explanation:\s*(.*)", wellness_score_raw, re.DOTALL)
    if explanation_match:
        wellness_score_explanation = explanation_match.group(1).strip()
    
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