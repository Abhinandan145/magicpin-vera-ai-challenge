"""
Pydantic data models for the magicpin Vera Merchant Engagement Engine HTTP API.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ContextPushRequest(BaseModel):
    scope: Literal["category", "merchant", "customer", "trigger"]
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str


class ContextPushResponse(BaseModel):
    accepted: bool
    ack_id: Optional[str] = None
    stored_at: Optional[str] = None
    reason: Optional[str] = None
    current_version: Optional[int] = None


class TickRequest(BaseModel):
    now: str
    available_triggers: List[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    send_as: Literal["vera", "merchant_on_behalf"] = "vera"
    trigger_id: str
    template_name: str
    template_params: List[str] = Field(default_factory=list)
    body: str
    cta: str = "open_ended"
    suppression_key: str
    rationale: str


class TickResponse(BaseModel):
    actions: List[ActionItem] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str = "merchant"
    message: str
    received_at: str
    turn_number: int = 1


class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str


class HealthzResponse(BaseModel):
    status: str = "ok"
    uptime_seconds: int
    contexts_loaded: Dict[str, int]


class MetadataResponse(BaseModel):
    team_name: str
    team_members: List[str]
    model: str
    approach: str
    contact_email: str
    version: str
    submitted_at: str
