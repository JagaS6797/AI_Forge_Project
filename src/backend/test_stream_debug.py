import asyncio
import os
from dotenv import load_dotenv

# Load env file before importing app components
load_dotenv('.env.development')

from app.services.research_digest_service import stream_research_digest

async def test_stream():
    topic = 'transformers in healthcare'
    max_papers = 3
    print(f'Starting stream for: {topic}')
    try:
        count = 0
        async for event in stream_research_digest(topic, max_papers):
            print(f'EVENT: {event}')
            count += 1
    except Exception as e:
        import traceback
        print('ERROR:')
        traceback.print_exc()
    print('Stream finished.')

if __name__ == '__main__':
    try:
        asyncio.run(asyncio.wait_for(test_stream(), timeout=90))
    except asyncio.TimeoutError:
        print('TIMED OUT after 90 seconds')
