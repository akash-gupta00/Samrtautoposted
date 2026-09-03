# ABC import kar rahe hain.
# Iska use abstract base class banane ke liye hota hai.
from abc import ABC, abstractmethod


# ============================================
# Base Social Provider
# ============================================

# Ye base class hai.
# Saare social providers isi ko inherit karenge.
class BaseProvider(ABC):

    # Platform se account connect karne ka method.
    @abstractmethod
    def connect(self):
        pass

    # Access token refresh karne ka method.
    @abstractmethod
    def refresh_token(self):
        pass

    # Social media par post publish karne ka method.
    @abstractmethod
    def publish_post(self, post):
        pass

    # Social media se post delete karne ka method.
    @abstractmethod
    def delete_post(self, platform_post_id):
        pass

    # Published post ki analytics lane ka method.
    @abstractmethod
    def fetch_analytics(self, platform_post_id):
        pass

    # Account disconnect karne ka method.
    @abstractmethod
    def disconnect(self):
        pass