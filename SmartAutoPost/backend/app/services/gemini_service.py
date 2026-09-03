from typing import Optional
from google.genai import types
from app.core.gemini_client import client
from app.schemas.gemini import GeminiResponse


class GeminiService:

    def generate(
        self, 
        data, 
        image_bytes: Optional[bytes] = None, 
        mime_type: str = "image/jpeg", 
        **kwargs
    ):
        tone = getattr(data, "tone", "engaging")
        language = getattr(data, "language", "en")
        task_type = getattr(data, "task_type", "caption")
        platform = getattr(data, "platform", "Instagram")
        keyword = getattr(data, "keyword", "") or "Engaging post"

        if task_type == "caption":
            prompt = f"""
You are an expert social media copywriter.

Generate only one catchy social media caption with relevant hashtags.
If an image is attached, analyze the image content carefully and write the caption based on it.

Keyword/Context: {keyword}
Platform: {platform}
Tone: {tone}
Language: {language}

Rules:
- Return only the final caption with hashtags
- Do not give multiple options
- Do not add explanations
- Do not add headings
- Add suitable emojis
"""

        elif task_type == "hashtags":
            prompt = f"""
Generate exactly 15 relevant social media hashtags.
If an image is attached, include hashtags relevant to what is visible in the image.

Keyword/Context: {keyword}
Platform: {platform}
Language: {language}

Rules:
- Return only hashtags
- Do not explain
- Do not add headings
- Keep all hashtags in one line
"""

        elif task_type == "seo":
            prompt = f"""
Generate SEO content for the following topic.

Keyword: {keyword}
Platform: {platform}
Language: {language}

Return exactly:
SEO Title:
Meta Description:
Keywords:

Do not add any explanation.
"""

        elif task_type == "image_prompt":
            prompt = f"""
Generate one professional AI image prompt.

Topic: {keyword}
Platform: {platform}
Tone: {tone}
Language: {language}

Rules:
- Return only the image prompt
- Do not explain
- Do not add headings
"""

        else:
            prompt = f"""
Generate useful social media content.

Keyword: {keyword}
Platform: {platform}
Task: {task_type}
Tone: {tone}
Language: {language}

Return only the final result.
"""

        try:
            contents = [prompt]

            # Agar image aayi hai toh Gemini payload me attach karein
            if image_bytes and len(image_bytes) > 0:
                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type or "image/jpeg"
                    )
                )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
            )

            result_text = response.text.strip() if hasattr(response, "text") and response.text else str(response)

        except Exception as e:
            # Safe fallback agar quota ya model error ho
            result_text = f"✨ {keyword}\n\nCheck out this post! Double tap if you agree. 🚀\n\n#trending #viral #{platform.lower()} #growth"

        return GeminiResponse(
            result=result_text,
            task_type=task_type,
            platform=platform,
            language=language,
        )