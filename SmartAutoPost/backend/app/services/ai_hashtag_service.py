from app.schemas.ai_hashtag import HashtagResponse


class AIHashtagService:

    def generate_hashtags(self, data):

        keyword = data.keyword.replace(" ", "")

        hashtags = [
            f"#{keyword}",
            "#AI",
            "#Automation",
            "#Business",
            "#Startup",
            "#Technology",
            "#Growth",
            "#DigitalMarketing",
            "#Innovation",
            "#SmartAutoPost",
        ]

        return HashtagResponse(
            hashtags=hashtags,
            platform=data.platform,
            language=data.language,
        )