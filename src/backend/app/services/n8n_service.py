"""n8n integration service for support triage workflow."""
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ticket import Ticket

logger = logging.getLogger(__name__)


def classify_intent(user_message: str) -> str:
    """
    Classify user message intent using keyword matching.
    
    Returns one of: escalation, sales, compliance, normal
    """
    message_lower = user_message.lower()
    
    # Escalation keywords
    escalation_keywords = {
        "urgent", "broken", "error", "not working", "can't access",
        "bug", "issue", "problem", "failed", "help me", "support",
        "emergency", "critical", "down", "crash", "stuck", "broken"
    }
    
    # Compliance/Security keywords  
    compliance_keywords = {
        "lawsuit", "legal", "gdpr", "privacy", "data breach",
        "security issue", "vulnerability", "personal data",
        "compliance", "regulatory", "audit", "breach", "security"
    }
    
    # Sales keywords
    sales_keywords = {
        "price", "pricing", "buy", "purchase", "plan", "upgrade",
        "enterprise", "cost", "trial", "demo", "quote", "sales",
        "discount", "license", "subscription", "billing", "payment"
    }
    
    # Check for keywords
    if any(kw in message_lower for kw in escalation_keywords):
        return "escalation"
    elif any(kw in message_lower for kw in compliance_keywords):
        return "compliance"
    elif any(kw in message_lower for kw in sales_keywords):
        return "sales"
    
    return "normal"


def get_priority_from_intent(intent: str) -> str:
    """Map intent type to ticket priority."""
    priority_map = {
        "escalation": "high",
        "compliance": "urgent",
        "sales": "medium",
        "normal": "low"
    }
    return priority_map.get(intent, "medium")


def get_assigned_team(intent: str) -> Optional[str]:
    """Get assigned team based on intent type."""
    team_map = {
        "escalation": "Support Team",
        "compliance": "Compliance Team",
        "sales": "Sales Team",
        "normal": None
    }
    return team_map.get(intent)


async def create_ticket_if_needed(
    db: AsyncSession,
    user_email: str,
    thread_id: str,
    user_message: str,
    assistant_message: Optional[str] = None,
    attachment_ids: Optional[list] = None,
    intent_type: Optional[str] = None,
) -> Optional[str]:
    """
    Create a support ticket if the message indicates escalation, sales, or compliance.
    
    Args:
        db: Database session
        user_email: User email address
        thread_id: Chat thread ID
        user_message: User's original message
        assistant_message: Assistant's response (for reference)
        attachment_ids: List of attachment UUIDs
        intent_type: Intent classification (if provided, use it; otherwise auto-classify)
    
    Returns:
        Ticket ID (ticket_id field) if created, None if not needed (normal intent)
    """
    try:
        # Classify intent if not provided
        if intent_type is None:
            intent_type = classify_intent(user_message)
        
        # Only create ticket for non-normal intents
        if intent_type == "normal":
            return None
        
        # Get priority and team from intent
        priority = get_priority_from_intent(intent_type)
        assigned_team = get_assigned_team(intent_type)
        
        # Generate unique ticket ID
        generated_ticket_id = f"TKT-{uuid4().hex[:12].upper()}"
        
        # Determine next action
        next_action_map = {
            "escalation": "Review and respond to customer immediately",
            "compliance": "Review for compliance implications",
            "sales": "Contact prospect for demo/pricing discussion",
            "normal": None
        }
        next_action = next_action_map.get(intent_type)
        
        # Create ticket
        ticket = Ticket(
            ticket_id=generated_ticket_id,
            user_email=user_email,
            thread_id=thread_id,
            issue=user_message[:500] if len(user_message) > 500 else user_message,
            category=intent_type.upper(),
            priority=priority,
            status="open",
            assigned_team=assigned_team,
            next_action=next_action
        )
        
        db.add(ticket)
        await db.flush()  # Flush to get the ID without committing
        
        logger.info(
            f"Created {intent_type} ticket {generated_ticket_id} for {user_email}",
            extra={
                "user_email": user_email,
                "thread_id": thread_id,
                "category": intent_type,
                "ticket_id": generated_ticket_id
            }
        )
        
        return generated_ticket_id
        
    except Exception as e:
        logger.warning(
            f"Failed to create ticket: {str(e)}",
            extra={
                "user_email": user_email,
                "thread_id": thread_id,
                "error": str(e)
            },
            exc_info=True
        )
        return None


async def notify_n8n(
    user_email: str,
    thread_id: str,
    user_message: str,
    assistant_message: str,
    attachment_ids: Optional[list] = None
) -> bool:
    """
    Send a webhook notification to n8n for support triage.
    
    Fire-and-forget pattern: never blocks chat, silently handles errors.
    
    Args:
        user_email: User email address
        thread_id: Chat thread ID
        user_message: User's original message
        assistant_message: Assistant's response
        attachment_ids: List of attachment UUIDs
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.n8n_webhook_url:
        logger.debug("n8n webhook URL not configured, skipping notification")
        return False
    
    try:
        # Classify to determine category
        intent = classify_intent(user_message)
        
        payload = {
            "user_email": user_email,
            "thread_id": thread_id,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "issue": user_message,
            "category": intent.upper(),
            "priority": get_priority_from_intent(intent),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Fire-and-forget with short timeout
        timeout = httpx.Timeout(settings.n8n_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        
        logger.debug(
            f"n8n webhook sent successfully for {user_email}",
            extra={"user_email": user_email, "thread_id": thread_id}
        )
        return True
        
    except httpx.TimeoutException:
        logger.warning(
            f"n8n webhook timeout for {user_email}",
            extra={"user_email": user_email, "thread_id": thread_id}
        )
        return False
        
    except Exception as e:
        logger.warning(
            f"n8n webhook failed for {user_email}: {str(e)}",
            extra={
                "user_email": user_email,
                "thread_id": thread_id,
                "error": str(e)
            }
        )
        return False
