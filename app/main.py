"""
FastAPI application for magicpin Vera Merchant Engagement Assistant.
Implements the 5 core judging and testing endpoints:
- GET  /v1/healthz
- GET  /v1/metadata
- POST /v1/context
- POST /v1/tick
- POST /v1/reply
"""

import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, APP_START_TIME
from app.models import (
    ContextPushRequest, ContextPushResponse,
    TickRequest, TickResponse,
    ReplyRequest, ReplyResponse,
    HealthzResponse, MetadataResponse
)
from app.context_store import context_store
from app.trigger_engine import trigger_engine
from app.conversation import conversation_engine

app = FastAPI(
    title="magicpin Vera Autonomous Merchant Engagement Engine",
    description="Stateful 4-context grounded engagement engine for magicpin merchants",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Seed context store with full expanded dataset on service startup."""
    context_store.load_from_dir()


@app.get("/", tags=["System"])
def root():
    """Root endpoint welcoming judge/evaluators and linking to health and documentation."""
    return {
        "service": "magicpin Vera Autonomous Merchant Engagement Engine",
        "team_name": settings.TEAM_NAME,
        "team_members": settings.TEAM_MEMBERS,
        "version": settings.VERSION,
        "status": "online",
        "endpoints": {
            "healthz": "/v1/healthz",
            "metadata": "/v1/metadata",
            "context": "/v1/context",
            "tick": "/v1/tick",
            "reply": "/v1/reply",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }




@app.get("/v1/healthz", response_model=HealthzResponse, tags=["System"])
def health_check():
    """Liveness probe reporting uptime and counts of 4-tier contexts loaded."""
    return HealthzResponse(
        status="ok",
        uptime_seconds=int(time.time() - APP_START_TIME),
        contexts_loaded=context_store.get_counts()
    )


@app.get("/v1/metadata", response_model=MetadataResponse, tags=["System"])
def metadata():
    """Returns team credentials, model identity, version, and architectural approach."""
    return MetadataResponse(
        team_name=settings.TEAM_NAME,
        team_members=settings.TEAM_MEMBERS,
        model=settings.LLM_MODEL,
        approach=settings.APPROACH,
        contact_email=settings.CONTACT_EMAIL,
        version=settings.VERSION,
        submitted_at=settings.SUBMITTED_AT
    )


@app.post("/v1/context", response_model=ContextPushResponse, tags=["Context"])
def push_context(req: ContextPushRequest):
    """
    Ingest a 4-tier context item (category, merchant, customer, trigger).
    Maintains monotonic versioning per (scope, context_id).
    Returns 409 Conflict if an older/stale version is provided.
    """
    success, result_or_reason, cur_ver = context_store.push_context(
        scope=req.scope,
        context_id=req.context_id,
        version=req.version,
        payload=req.payload,
        delivered_at=req.delivered_at
    )
    
    if not success:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "accepted": False,
                "reason": "stale_version",
                "current_version": cur_ver
            }
        )
    
    return ContextPushResponse(
        accepted=True,
        ack_id=result_or_reason,
        stored_at=datetime.utcnow().isoformat() + "Z"
    )


@app.post("/v1/tick", response_model=TickResponse, tags=["Triggers"])
def process_tick(req: TickRequest):
    """
    Evaluate available active triggers for eligible merchants.
    Applies suppression filtering, deduplication, and domain composition.
    """
    try:
        actions = trigger_engine.process_tick(
            available_trigger_ids=req.available_triggers,
            now_str=req.now
        )
        return TickResponse(actions=actions)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tick evaluation failed: {str(e)}"
        )


@app.post("/v1/reply", response_model=ReplyResponse, tags=["Conversation"])
def process_reply(req: ReplyRequest):
    """
    Handle merchant/customer reply.
    Performs multi-language auto-reply detection, backoff scheduling,
    intent routing (Commitment -> Action, Hostile -> Opt-out, Off-topic -> Redirection).
    """
    try:
        res = conversation_engine.handle_reply(
            conversation_id=req.conversation_id,
            message=req.message,
            turn_number=req.turn_number,
            merchant_id=req.merchant_id,
            customer_id=req.customer_id,
            from_role=req.from_role
        )
        return ReplyResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reply handling failed: {str(e)}"
        )
