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
    You are an expert ATS (Applicant Tracking System) and professional resume evaluator. Your task is to analyze the provided resume against the given job description and calculate an ATS compatibility score.

    **Instructions for your response:**
    1.  Carefully compare the resume's skills, experience, and keywords with the job description's requirements.
    2.  Provide an ATS compatibility score from 0 to 100.
    3.  Provide a detailed analysis explaining the score. The analysis MUST include sections for "Matching Skills", "Missing Keywords", and "Suggestions for Improvement".
    4.  Use markdown for formatting. Each section heading MUST be on its own line and formatted as a level 3 markdown heading (e.g., ### Matching Skills).
    5.  Maintain a professional tone. Do not use informal language or emojis.
    
    **Resume Text:**
    {resume_text}

    **Job Description:**
    {job_description}

    ---
    **Output Format:**
    Your response MUST strictly follow this format, starting with the score on the first line. Do not add any text before the score or after the final suggestion.

    ATS Score: [score]/100

    ### Matching Skills
    [Your analysis for this section]

    ### Missing Keywords
    [Your analysis for this section]

    ### Suggestions for Improvement
    [Your analysis for this section]
    """

    # Get the raw response from our key-rotating function
    response_text = await make_gemini_request(prompt)

    # Check if the master request function returned an error message
    if "Error:" in response_text or "All available API keys" in response_text:
        return {"score": 0, "analysis": response_text}

    # Parse the successful response
    score_match = re.search(r"ATS Score:\s*(\d+)/100", response_text, re.IGNORECASE)
    score = int(score_match.group(1)) if score_match else 0
    
    # The analysis is everything after the score line.
    # Find the end of the first line to start capturing the analysis.
    first_line_end = response_text.find('\n')
    if first_line_end != -1:
        analysis = response_text[first_line_end:].strip()
    else:
        analysis = "Could not parse analysis from the AI response."

    return {"score": score, "analysis": analysis}