from app.core.gemini_client import client
from app.schemas.gemini import GeminiResponse


class GeminiService:

    def generate(self, data):

        if data.task_type == "caption":

            prompt = f"""
You are an expert social media copywriter.

Generate only one social media caption.

Keyword: {data.keyword}
Platform: {data.platform}
Tone: {data.tone}
Language: {data.language}

Rules:
- Return only the final caption
- Do not give multiple options
- Do not add explanations
- Do not add headings
- Add suitable emojis only when useful
"""

        elif data.task_type == "hashtags":

            prompt = f"""
Generate exactly 15 relevant social media hashtags.

Keyword: {data.keyword}
Platform: {data.platform}
Language: {data.language}

Rules:
- Return only hashtags
- Do not explain
- Do not add headings
- Keep all hashtags in one line
"""

        elif data.task_type == "seo":

            prompt = f"""
Generate SEO content for the following topic.

Keyword: {data.keyword}
Platform: {data.platform}
Language: {data.language}

Return exactly:
SEO Title:
Meta Description:
Keywords:

Do not add any explanation.
"""

        elif data.task_type == "image_prompt":

            prompt = f"""
Generate one professional AI image prompt.

Topic: {data.keyword}
Platform: {data.platform}
Tone: {data.tone}
Language: {data.language}

Rules:
- Return only the image prompt
- Do not explain
- Do not add headings
"""

        else:

            prompt = f"""
Generate useful social media content.

Keyword: {data.keyword}
Platform: {data.platform}
Task: {data.task_type}
Tone: {data.tone}
Language: {data.language}

Return only the final result.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return GeminiResponse(
            result=response.text.strip(),
            task_type=data.task_type,
            platform=data.platform,
            language=data.language,
        )