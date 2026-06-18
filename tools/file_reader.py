import os
import PyPDF2

TEXT_FILE_TYPES = [
    ".txt", ".py", ".js", ".html", ".css", ".json",
    ".md", ".csv", ".log", ".xml", ".yaml", ".yml"
]

IMAGE_FILE_TYPES = [
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"
]

# --- NEW: Added PDF support ---
PDF_FILE_TYPES = [
    ".pdf"
]

def read_file_preview(file_path: str, max_chars: int = 5000) -> dict:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # --- NEW: PDF Handling Logic ---
    if ext in PDF_FILE_TYPES:
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                content = ""
                
                # Extract text page by page
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        content += extracted + "\n"
                    
                    # Stop reading if we hit the character limit to save memory
                    if len(content) > max_chars:
                        content = content[:max_chars] + "... [Text Truncated]"
                        break
            
            return {
                "success": True,
                "type": "pdf",
                "file_path": file_path,
                "content": content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read PDF: {str(e)}"
            }

    # --- EXISTING: Text Handling Logic ---
    if ext in TEXT_FILE_TYPES:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read(max_chars)

            return {
                "success": True,
                "type": "text",
                "file_path": file_path,
                "content": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # --- EXISTING: Image Handling Logic ---
    if ext in IMAGE_FILE_TYPES:
        return {
            "success": True,
            "type": "image",
            "file_path": file_path,
            "content": (
                "Image file attached. Current text-based AI flow cannot visually inspect image pixels yet. "
                "A vision-capable AI model is needed for real image understanding."
            )
        }

    # --- EXISTING: Unknown File Logic ---
    try:
        size = os.path.getsize(file_path)
        return {
            "success": True,
            "type": "unknown",
            "file_path": file_path,
            "content": (
                f"File attached: {file_path}\n"
                f"File size: {size} bytes\n"
                "Preview unavailable for this file type."
            )
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }