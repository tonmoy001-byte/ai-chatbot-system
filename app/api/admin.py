from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import os

from app.database import get_db
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/admin", tags=["admin"])

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Admin dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request):
    """Conversations list page."""
    return templates.TemplateResponse("conversations.html", {"request": request})


@router.get("/conversations/{conversation_id}", response_class=HTMLResponse)
async def conversation_detail_page(request: Request, conversation_id: str):
    """Conversation detail page."""
    return templates.TemplateResponse("conversation_detail.html", {
        "request": request,
        "conversation_id": conversation_id
    })


# API Endpoints
@router.get("/api/conversations")
async def list_conversations_api(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List conversations API."""
    conversation_service = ConversationService(db)
    conversations = await conversation_service.list_conversations(
        status=status,
        limit=limit,
        offset=offset
    )
    return {"conversations": conversations, "count": len(conversations)}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation_api(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get conversation with messages API."""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.get("/api/stats")
async def get_stats_api(db: Session = Depends(get_db)):
    """Get statistics API."""
    conversation_service = ConversationService(db)
    stats = await conversation_service.get_stats()
    return stats


@router.post("/api/conversations/{conversation_id}/messages")
async def add_message_api(
    conversation_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Add message to conversation (for agent responses)."""
    body = await request.json()
    content = body.get("content")
    sender_type = body.get("sender_type", "agent")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    conversation_service = ConversationService(db)
    message = await conversation_service.add_message(
        conversation_id=conversation_id,
        sender_type=sender_type,
        content_type="text",
        content=content,
        db=db
    )
    
    return {"message_id": str(message.id), "status": "sent"}


# Keep existing endpoints
@router.get("/conversations-list")
async def list_conversations(
    status: str = "active",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all conversations with optional filtering."""
    conversation_service = ConversationService(db)
    conversations = await conversation_service.list_conversations(
        status=status,
        limit=limit,
        offset=offset
    )
    return {"conversations": conversations, "count": len(conversations)}


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get conversation with messages."""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.get("/stats-data")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    conversation_service = ConversationService(db)
    stats = await conversation_service.get_stats()
    return stats


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
