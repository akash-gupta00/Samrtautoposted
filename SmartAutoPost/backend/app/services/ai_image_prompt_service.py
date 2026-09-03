from app.schemas.ai_image_prompt import ImagePromptResponse


class AIImagePromptService:

    def generate_image_prompt(self, data):

        prompt = (
            f"Create a {data.style} social media image for {data.keyword}. "
            f"Use clean layout, professional colors, high-quality design, "
            f"business branding, eye-catching visual, suitable for {data.platform}."
        )

        return ImagePromptResponse(
            image_prompt=prompt,
            platform=data.platform,
            style=data.style,
            language=data.language,
        )