import os
import google.generativeai as genai
from app.core.config import settings
from app.schemas.gemini import GeminiRequest

# API key configure karein
api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


class GeminiService:
    def __init__(self):
        # Multimodal Gemini model
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate(self, req: GeminiRequest, image_bytes: bytes = None, mime_type: str = "image/jpeg", **kwargs):
        """
        Text prompt aur Image bytes dono ko safely handle karta hai.
        """
        task = getattr(req, "task_type", "caption")
        platform = getattr(req, "platform", "Instagram")
        user_keyword = getattr(req, "keyword", "") or "Engaging post"

        prompt_text = (
            f"You are a social media expert. Task: {task}. "
            f"Platform: {platform}. "
            f"User context/prompt: {user_keyword}. "
            f"Analyze the image (if provided) and generate a catchy, viral caption with relevant trending hashtags."
        )

        try:
            content_parts = [prompt_text]

            # Agar image aayi hai toh multimodal payload me add karein
            if image_bytes and len(image_bytes) > 0:
                content_parts.append({
                    "mime_type": mime_type or "image/jpeg",
                    "data": image_bytes
                })

            response = self.model.generate_content(content_parts)
            
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return str(response)

        except Exception as e:
            # Fallback agar API quota ya response me error aaye
            return (
                f"🚀 {user_keyword}\n\n"
                f"Check out this update! Double tap if you find this useful. ✨\n\n"
                f"#trending #viral #growth #{platform.lower()} #explore"
            )