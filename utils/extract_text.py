# utils/extract_text.py
import fitz  # This is the PyMuPDF library
from fastapi import UploadFile
import io

async def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    """
    Extracts plain text from an uploaded PDF file.

    Args:
        pdf_file: The uploaded PDF file object from FastAPI.

    Returns:
        A string containing all the text from the PDF, or an empty string if an error occurs.
    """
    try:
        # Read the file's content into bytes from the UploadFile object.
        # This is necessary because PyMuPDF works with file paths or byte streams.
        pdf_bytes = await pdf_file.read()
        
        # Open the PDF directly from the byte stream.
        # This avoids saving the file to disk.
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        text = ""
        # Iterate through each page in the document.
        for page in doc:
            # Extract the text from the current page and append it.
            text += page.get_text()
            
        doc.close()
        return text
    except Exception as e:
        # If any error occurs during extraction, print it and return an empty string.
        print(f"Error extracting text from PDF: {e}")
        return ""