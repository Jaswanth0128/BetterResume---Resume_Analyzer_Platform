# utils/simple_ats.py
import re
# We now only need to import our master request function
from .api_key_manager import make_gemini_request

async def calculate_ats_score(resume_text: str, job_description: str) -> dict:
    """
    Calculates an ATS score by delegating the request to the key manager
    and then parsing the successful response.
    """
    # Using the detailed prompt you provided
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

    # Get the raw response from our key-rotating function
    response_text = await make_gemini_request(prompt)

    # Check if the master request function returned an error message
    if "Error:" in response_text or "All available API keys" in response_text:
        return {"score": 0, "analysis": response_text}

    # Parse the successful response
    score_match = re.search(r"ATS Score:\s*(\d+)/100", response_text, re.IGNORECASE)
    score = int(score_match.group(1)) if score_match else 0
    
    # Use a flexible search to find the start of the analysis
    analysis_match = re.search(r'analysis:', response_text, re.IGNORECASE)
    analysis = response_text[analysis_match.end():].strip() if analysis_match else "Could not parse analysis from the AI response."

    return {"score": score, "analysis": analysis}