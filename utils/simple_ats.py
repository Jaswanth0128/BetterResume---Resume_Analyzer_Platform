# utils/simple_ats.py
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
# Set up the Gemini API client and model
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    model = None

async def calculate_ats_score(resume_text: str, job_description: str) -> dict:
    """
    Calculates an ATS score by comparing a resume to a job description.

    This function sends the resume and job description to the Gemini API
    and parses the response to extract a numeric score and a detailed analysis.

    Returns:
        A dictionary containing the 'score' (int) and 'analysis' (str).
    """
    if not model:
        return {"score": 0, "analysis": "Error: Gemini model is not configured."}

    # --- Refined Prompt ---
    # This prompt provides clearer instructions and asks for a structured,
    # markdown-formatted analysis for better readability on the frontend.
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and professional resume evaluator.

    Your task is to analyze the provided resume against the given job description and calculate an ATS compatibility score.

    **Instructions:**
    1.  Carefully compare the resume's skills, experience, and keywords with the job description's requirements.
    2.  Provide an ATS compatibility score from 0 to 100.
    3.  Provide a detailed analysis explaining the score. The analysis MUST include sections(Section names in bold) for "**1. Matching Skills**", "**2.  Missing Keywords**", and "**3. Suggestions for Improvement**" using markdown.
    4.  Maintain professionalism throughout the response, dont use informal language.
    **Resume Text:**
    {resume_text}

    **Job Description:**
    {job_description}

    ---
    **Output Format:**
    Your response MUST strictly follow this format, with the score on the first line:
    ATS Score: [score]/100

    **Analysis:**
    [Your detailed analysis with the required markdown sections]
    """

    try:
        response = await model.generate_content_async(prompt)
        response_text = response.text

        # --- Response Parsing ---
        # Use regular expressions to reliably extract the score and analysis.
        score_match = re.search(r"ATS Score:\s*(\d+)/100", response_text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 0
        
        # The analysis is everything that comes after the "Analysis:" heading.
        analysis_parts = re.split(r"\*\*Analysis:\*\*", response_text, flags=re.IGNORECASE)
        analysis = analysis_parts[1].strip() if len(analysis_parts) > 1 else "Could not parse analysis."

        return {"score": score, "analysis": analysis}
        
    except Exception as e:
        return {"score": 0, "analysis": f"An error occurred during ATS analysis: {e}"}