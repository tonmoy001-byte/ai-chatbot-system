from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.config import get_settings
from app.services.facebook import FacebookService
from app.services.instagram import InstagramService
from app.services.message_router import MessageRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhooks"])
settings = get_settings()


@router.get("/facebook")
async def verify_facebook_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str
):
    """Verify Facebook webhook subscription."""
    logger.info(f"Facebook webhook verification: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.FACEBOOK_VERIFY_TOKEN:
        logger.info("Facebook webhook verified successfully")
        return int(hub_challenge)
    
    logger.warning("Facebook webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/facebook")
async def handle_facebook_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """Handle incoming Facebook messages."""
    body = await request.body()
    
    # Verify signature
    facebook_service = FacebookService()
    if not facebook_service.verify_signature(body, x_hub_signature_256):
        logger.warning("Invalid Facebook webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Facebook webhook payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    logger.info(f"Received Facebook webhook: {payload.get('object')}")
    
    # Process each entry
    for entry in payload.get("entry", []):
        page_id = entry.get("id")
        events = entry.get("messaging", [])
        
        for event in events:
            try:
                await facebook_service.process_event(event, db)
            except Exception as e:
                logger.error(f"Error processing Facebook event: {str(e)}")
                continue
    
    return {"status": "ok"}


@router.get("/instagram")
async def verify_instagram_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str
):
    """Verify Instagram webhook subscription."""
    logger.info(f"Instagram webhook verification: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.FACEBOOK_VERIFY_TOKEN:
        logger.info("Instagram webhook verified successfully")
        return int(hub_challenge)
    
    logger.warning("Instagram webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/instagram")
async def handle_instagram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """Handle incoming Instagram messages."""
    body = await request.body()
    
    # Verify signature
    instagram_service = InstagramService()
    if not instagram_service.verify_signature(body, x_hub_signature_256):
        logger.warning("Invalid Instagram webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Instagram webhook payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    logger.info(f"Received Instagram webhook: {payload.get('object')}")
    
    # Process each entry
    for entry in payload.get("entry", []):
        events = entry.get("messaging", [])
        
        for event in events:
            try:
                await instagram_service.process_event(event, db)
            except Exception as e:
                logger.error(f"Error processing Instagram event: {str(e)}")
                continue
    
    return {"status": "ok"}


# Test endpoint for development
@router.post("/test/facebook")
async def test_facebook_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Test endpoint for Facebook webhook (development only)."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    payload = await request.json()
    
    # Create a mock event from test payload
    event = {
        "sender": {"id": payload.get("sender_id", "test_user")},
        "message": {
            "text": payload.get("message", "Hello"),
            "mid": "test_message_id"
        },
        "timestamp": payload.get("timestamp", "1234567890")
    }
    
    facebook_service = FacebookService()
    response = await facebook_service.process_event(event, db)
    
    return {"response": response}


@router.post("/test/instagram")
async def test_instagram_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Test endpoint for Instagram webhook (development only)."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    payload = await request.json()
    
    # Create a mock event from test payload
    event = {
        "sender": {"id": payload.get("sender_id", "test_user")},
        "message": {
            "text": payload.get("message", "Hello"),
            "mid": "test_message_id"
        },
        "timestamp": payload.get("timestamp", "1234567890")
    }
    
    instagram_service = InstagramService()
    response = await instagram_service.process_event(event, db)
    
    return {"response": response}
