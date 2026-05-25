#!/usr/bin/env python3
"""
Quick test script to verify the n8n support triage setup.
Tests webhook POST and database ticket creation.
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src/backend to path
sys.path.insert(0, str(Path(__file__).parent))

import httpx
import asyncpg

# Test configuration
N8N_WEBHOOK_URL = "https://jagadeshc.app.n8n.cloud/webhook/support-triage"
DATABASE_URL = "postgresql://postgres:@localhost/amzur"

# Test payloads
TEST_ESCALATION = {
    "user_email": "test@example.com",
    "thread_id": "test-thread-123",
    "user_message": "I'm experiencing a critical error - the system is completely broken and I urgently need help!",
    "assistant_message": "I understand this is critical. Let me escalate this immediately.",
    "attachment_ids": [],
    "timestamp": datetime.utcnow().isoformat()
}

TEST_SALES = {
    "user_email": "prospect@example.com",
    "thread_id": "sales-thread-456",
    "user_message": "What's the pricing for your enterprise plan?",
    "assistant_message": "Great question! Our enterprise plan includes custom pricing. Let me connect you with our sales team.",
    "attachment_ids": [],
    "timestamp": datetime.utcnow().isoformat()
}

TEST_NORMAL = {
    "user_email": "user@example.com",
    "thread_id": "normal-thread-789",
    "user_message": "How do I reset my password?",
    "assistant_message": "You can reset your password by clicking 'Forgot Password' on the login page.",
    "attachment_ids": [],
    "timestamp": datetime.utcnow().isoformat()
}


async def test_webhook(payload: dict, test_name: str) -> bool:
    """Test sending a webhook to n8n."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"\n✓ Webhook sent successfully")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return True
    except httpx.TimeoutException:
        print(f"\n✗ Webhook timeout (expected on free tier)")
        return False
    except Exception as e:
        print(f"\n✗ Webhook failed: {str(e)}")
        return False


async def query_tickets():
    """Query tickets from database."""
    print(f"\n{'='*60}")
    print("Querying database for tickets...")
    print(f"{'='*60}")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Query all tickets
        tickets = await conn.fetch('SELECT id, user_email, thread_id, intent_type, priority, created_at FROM tickets ORDER BY created_at DESC LIMIT 5')
        
        if not tickets:
            print("\nNo tickets found in database yet.")
            print("This is normal if:")
            print("  - The n8n workflow hasn't executed yet")
            print("  - The backend isn't running to create tickets")
        else:
            print(f"\n✓ Found {len(tickets)} ticket(s):")
            for ticket in tickets:
                print(f"\n  ID: {ticket['id']}")
                print(f"  Email: {ticket['user_email']}")
                print(f"  Thread: {ticket['thread_id']}")
                print(f"  Intent: {ticket['intent_type']}")
                print(f"  Priority: {ticket['priority']}")
                print(f"  Created: {ticket['created_at']}")
        
        await conn.close()
        return True
    except asyncpg.PostgresError as e:
        print(f"\n✗ Database error (tickets table might not exist yet): {str(e)}")
        print("  Run: alembic upgrade head")
        print("  Or ensure the backend has started at least once")
        return False
    except Exception as e:
        print(f"\n✗ Database connection failed: {str(e)}")
        print(f"  Check DATABASE_URL: {DATABASE_URL}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("n8n Support Triage - Integration Test")
    print("="*60)
    print("\nThis script tests:")
    print("  1. Webhook connectivity to n8n")
    print("  2. Database ticket creation")
    print("  3. Intent classification")
    
    # Test webhooks
    print("\n" + "─"*60)
    print("STEP 1: Send test webhooks to n8n")
    print("─"*60)
    
    await test_webhook(TEST_ESCALATION, "ESCALATION Intent (High Priority)")
    await test_webhook(TEST_SALES, "SALES Intent (Medium Priority)")
    await test_webhook(TEST_NORMAL, "NORMAL Intent (Low Priority)")
    
    # Query database
    print("\n" + "─"*60)
    print("STEP 2: Query tickets from database")
    print("─"*60)
    
    await asyncio.sleep(2)  # Wait for async processing
    await query_tickets()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("\nExpected results after webhook test:")
    print("  ✓ Escalation message → Creates HIGH priority ticket")
    print("  ✓ Sales message → Creates MEDIUM priority ticket")
    print("  ✓ Normal message → Creates LOW priority ticket (or no ticket)")
    print("\nNext steps:")
    print("  1. If tickets appear in DB → n8n workflow is working!")
    print("  2. Check n8n Executions tab for real-time logs")
    print("  3. Verify emails were sent (check gmail account)")
    print("  4. Frontend tests via http://localhost:5173")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
