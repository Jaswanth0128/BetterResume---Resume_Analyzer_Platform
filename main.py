import os
import re
import markdown
import logging
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from datetime import datetime

# Import utility functions
from utils.extract_text import extract_text_from_pdf
from utils.gemini_api import get_summary, get_analysis, get_wellness_score
from utils.simple_ats import calculate_ats_score

# Load environment variables (local dev only; in Cloud Run use env vars/Secret Manager)
load_dotenv()

# Configure logging (Cloud Run logs will capture this)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Simple health check for Cloud Run monitoring."""
    return {"status": "ok"}


# --- Upload Page ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


# --- Resume Analysis Endpoint ---
@app.post("/analyze", response_class=HTMLResponse)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form("")
):
    """Process uploaded resume and optional job description, then render results."""

    # 1. Validate file type
    if resume.content_type != "application/pdf":
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": "Invalid file type. Please upload a PDF."}
        )

    # 2. Extract text
    resume_text = await extract_text_from_pdf(resume)
    if not resume_text.strip():
        error_message = "Could not find any text to analyze. Ensure your PDF is text-based."
        return templates.TemplateResponse("upload.html", {"request": request, "error": error_message})

    # 3. AI Analysis
    current_date_str = datetime.now().strftime("%B %d, %Y")

    summary = await get_summary(resume_text)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to get summary from AI.")

    try:
        detailed_analysis = await get_analysis(resume_text=resume_text, current_date=current_date_str)
        if not detailed_analysis:
            raise HTTPException(status_code=500, detail="Failed to get detailed analysis from AI.")

        wellness_score_raw = await get_wellness_score(
            analysis_text=detailed_analysis,
            current_date=current_date_str
        )
        if not wellness_score_raw:
            raise HTTPException(status_code=500, detail="Failed to get wellness score from AI.")

    except Exception as e:
        logger.error(f"AI Analysis Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during AI analysis.")

    # 4. Parse Wellness Score
    wellness_score_value = None
    wellness_score_explanation = "Could not parse wellness score."

    score_match = re.search(r"Score:\s*([0-9.]+)", wellness_score_raw)
    if score_match:
        wellness_score_value = float(score_match.group(1))

    explanation_match = re.search(r"Explanation:\s*(.*?)(?:\nNote:|$)", wellness_score_raw, re.DOTALL)
    if explanation_match:
        wellness_score_explanation = explanation_match.group(1).strip()

    wellness_score_percent = wellness_score_value * 10 if wellness_score_value else 0

    # 5. Convert Markdown to HTML
    detailed_analysis_html = markdown.markdown(detailed_analysis)

    # 6. ATS Scoring
    ats_score, ats_analysis_html, jd_provided = 0, "", bool(job_description.strip())
    if jd_provided:
        ats_result = await calculate_ats_score(resume_text, job_description)
        ats_score = ats_result.get("score", 0)
        ats_analysis_html = markdown.markdown(ats_result.get("analysis", ""))

    # 7. Context for template
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

    # 8. Render results
    return templates.TemplateResponse("result.html", context)


# --- Entrypoint for Cloud Run ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))  # Cloud Run sets PORT env var
    uvicorn.run("main:app", host="0.0.0.0", port=port)
