import os
from playwright.sync_api import Playwright

def pytest_configure():
    """Configure pytest for Playwright tests."""
    pass

# Playwright configuration
class PlaywrightConfig:
    """Configuration for Playwright tests."""
    
    # Base URL for the application
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

    # Browser settings
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    BROWSER = os.getenv("BROWSER", "chromium")
    
    # Timeouts
    TIMEOUT = 30000  # 30 seconds
    
    # Screenshots and videos
    SCREENSHOT_ON_FAILURE = True
    VIDEO_ON_FAILURE = True
    
    # Test data
    TEST_USER = {
        "username": "testuser_e2e",
        "email": "testuser_e2e@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }
    
    TEST_USER_2 = {
        "username": "testuser2_e2e",
        "email": "testuser2_e2e@example.com",
        "first_name": "Test",
        "last_name": "User2",
        "password": "TestPassword456!",
        "confirm_password": "TestPassword456!"
    }
