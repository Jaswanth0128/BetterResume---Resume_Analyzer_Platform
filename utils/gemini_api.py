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

async def get_analysis(resume_text: str) -> str:
    """
    Provides a detailed, section-wise analysis of the resume's quality.
    """
    prompt = f"""
    As an expert HR analyst and ATS specialist, provide a comprehensive analysis of this resume.

    Full Resume Text:
    {resume_text}

    Please analyze and provide detailed feedback on:
    1. **ATS Compatibility & Format**: Section organization, headers, keyword optimization.
    2. **Content Quality & Structure**: Summary effectiveness, work experience, skills, education, contact info.
    3. **Experience & Achievements**: Quantifiable metrics, career progression, relevance, impact.
    4. **Skills & Technical Competencies**: Hard vs soft skills, industry tech, categorization, gaps.
    5. **Areas for Improvement**: Missing sections, weak points, formatting suggestions.
    6. **Overall Strengths**: Standout qualities, competitive advantages, well-executed sections.

    Provide specific, actionable recommendations for each area in a section-wise markdown format.
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