from app.schemas.ai_seo import SEOResponse


class AISEOService:

    def generate_seo(self, data):

        clean_keyword = data.keyword.lower().replace(" ", "-")

        return SEOResponse(
            title=f"Best {data.keyword} Solution for Business Growth",
            meta_description=f"Discover how {data.keyword} can help your business grow faster with smart automation, better productivity, and digital transformation.",
            keywords=[
                data.keyword,
                f"{data.keyword} solution",
                f"{data.keyword} software",
                "business automation",
                "digital growth",
                "smart tools",
                clean_keyword,
            ],
            platform=data.platform,
            language=data.language,
        )