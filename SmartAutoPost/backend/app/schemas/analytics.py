from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    total_posts: int
    draft_posts: int
    scheduled_posts: int
    published_posts: int
    failed_posts: int
    connected_accounts: int