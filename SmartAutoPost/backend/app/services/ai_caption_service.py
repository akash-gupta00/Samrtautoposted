from app.schemas.ai_caption import CaptionResponse


class AICaptionService:

    def generate_caption(self, data):

        caption = (
            f"{data.keyword} ke liye ek {data.tone} caption.\n\n"
            f"🚀 {data.keyword} se apne business ko next level par le jao.\n"
            f"Aaj hi smart automation ka use karo aur apna time bachao.\n\n"
            f"#Automation #Business #Growth"
        )

        return CaptionResponse(
            caption=caption,
            platform=data.platform,
            tone=data.tone,
            language=data.language,
        )