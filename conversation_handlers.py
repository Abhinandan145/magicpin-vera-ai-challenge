"""
Vera Multi-Turn Conversation Handler.
Provides the standard `respond()` interface for conversational testing and simulations.
"""

from typing import List, Dict, Any, Optional
from app.context_store import context_store
from app.conversation import conversation_engine


def respond(
    incoming_message: str,
    conversation_id: str = "conv_default",
    turn_number: int = 1,
    merchant_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    from_role: str = "merchant"
) -> Dict[str, Any]:
    """
    Process an incoming message in a multi-turn conversation.

    Args:
        incoming_message: Text received.
        conversation_id: Unique conversation identifier.
        turn_number: Turn number in the dialog.
        merchant_id: Target merchant ID.
        customer_id: Customer ID if delegated.
        from_role: "merchant" or "customer".

    Returns:
        Dict with keys: action, body (or reply_text), cta, rationale, wait_seconds
    """
    res = conversation_engine.handle_reply(
        conversation_id=conversation_id,
        message=incoming_message,
        turn_number=turn_number,
        merchant_id=merchant_id,
        customer_id=customer_id,
        from_role=from_role
    )
    return res
