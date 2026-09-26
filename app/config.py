"""
Configuration settings for the magicpin Vera Merchant Engagement Engine.
"""

import os
import time

APP_START_TIME = time.time()
DEFAULT_SUBMITTED_AT = "2026-04-26T08:00:00Z"

class Settings:
    TEAM_NAME: str = os.getenv("TEAM_NAME", "Rajeev Karakoti")
    TEAM_MEMBERS: list = [m.strip() for m in os.getenv("TEAM_MEMBERS", "Rajeev Karakoti").split(",")]
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", "rajeev.karakoti@example.com")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SUBMITTED_AT: str = os.getenv("SUBMITTED_AT", DEFAULT_SUBMITTED_AT)
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "").lower()
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash" if os.getenv("LLM_PROVIDER") == "gemini" else "gpt-4o-mini")
    
    # Approach description
    APPROACH: str = (
        "Stateful 4-context grounded engagement engine with deterministic domain intelligence, "
        "intent-handoff execution router, WhatsApp auto-reply backoff, and category-native voice synthesis"
    )
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Operational limits
    MAX_ACTIONS_PER_TICK: int = int(os.getenv("MAX_ACTIONS_PER_TICK", "20"))
    CALL_TIMEOUT_SECONDS: int = int(os.getenv("CALL_TIMEOUT_SECONDS", "30"))

settings = Settings()
