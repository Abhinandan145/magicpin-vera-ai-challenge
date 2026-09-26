"""
Vera Autonomous Merchant Engagement Bot.
Entrypoint providing:
1. `compose(merchant, trigger, category, customer=None)` for direct message composition.
2. CLI / HTTP runner via uvicorn.
"""

from typing import Dict, Any, Optional
from app.composer import composer
from app.context_store import context_store


def compose(
    merchant: Optional[Dict[str, Any]],
    trigger: Dict[str, Any],
    category: Optional[Dict[str, Any]] = None,
    customer: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Direct composition entrypoint.
    Returns the complete action dictionary containing body, cta, rationale, etc.
    """
    return composer.compose(category, merchant, trigger, customer)


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    print(f"Starting Vera Merchant Engagement Engine on {settings.HOST}:{settings.PORT}...")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
