# utils/gemini_api.py

# We now only need to import our master request function
from .api_key_manager import make_gemini_request

# --- AI Functions (now simplified to use the key manager) ---

async def get_summary(resume_text: str) -> str:
    """
    Generates a concise professional summary from the resume text.
    """
    prompt = f"""
    Analyze the following resume and provide a concise summary in 4-5 sentences that captures:
    1. The candidate's professional level and main expertise
    2. Key skills and technologies
    3. Years of experience (if mentioned)
    4. Most recent or notable position
    5. Career focus or specialization

    Resume Text:
    {resume_text}

    Summary:
    """
    # Delegate the entire request process to the key manager
    return await make_gemini_request(prompt)

async def get_analysis(resume_text: str, current_date: str) -> str:
    """
    Provides a detailed, section-wise analysis of the resume's quality.
    """
    prompt = f"""
    You are an expert HR analyst and resume writing coach. The current date is {current_date}. Analyze all dates in the resume relative to this date.

    Your task is to provide a professional, section-by-section analysis of the provided resume.

    **Instructions:**
    1.  Analyze the resume based on the sections below.
    2.  For each section, provide specific, actionable recommendations for improvement.
    3.  Use markdown for formatting. Each section heading MUST be on its own line and formatted as a level 3 markdown heading (e.g., ### ATS Compatibility & Format).
    4.  Do NOT include any introductory title, preamble, or summary of your own (e.g., do not write "Resume Analysis for..." or "This analysis assesses..."). Start directly with the first section heading.
    5.  Maintain a professional tone. Do not use informal language or emojis.

    **Resume Text:**
    {resume_text}

    ---
    **Analysis Sections to Cover:**
    - ### ATS Compatibility & Format
    - ### Content Quality & Structure
    - ### Experience & Achievements
    - ### Skills & Technical Competencies
    - ### Areas for Improvement
    - ### Overall Strengths

    Begin your response with the first section.
    """
    # Delegate the entire request process to the key manager
    return await make_gemini_request(prompt)

async def get_wellness_score(analysis_text: str, current_date: str) -> str:
    """
    Generates a wellness score based on the detailed analysis provided.
    """
    prompt = f"""
    The current date is {current_date}. You must evaluate all dates on the resume relative to this date.

    Based on the resume analysis provided below, provide a "Wellness Score" from 0.0 to 10.0.

    **Scoring Factors (Do NOT penalize the score for a missing summary):**
    - ATS compatibility (25%)
    - Content quality and relevance (25%)
    - Professional presentation (20%)
    - Completeness of information (15%)
    - Achievement quantification (15%)

    **Additional Check (Separate from score):**
    - After the explanation, add a "Note:" section ONLY IF a professional summary or objective is missing.

    **Analysis:**
    {analysis_text}

    **Output Format:**
    Provide your response in this exact format. The "Note:" section is optional and should only appear if a summary is missing.

    Score: X.X
    Explanation: [Brief 2-3 sentence explanation of the score based on the factors above.]
    Note: [This resume is missing a professional summary, which is highly recommended.]
    """
    # Delegate the entire request process to the key manager
    return await make_gemini_request(prompt)