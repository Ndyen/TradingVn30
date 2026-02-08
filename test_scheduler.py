"""
Test scheduler to verify it works before running Start_Bot.bat
This runs the pipeline once (like Start_Bot would trigger)
"""
import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.app.core.scheduler import pipeline_job

async def test():
    print("\n" + "=" * 60)
    print("TESTING SCHEDULER PIPELINE (Simulating Start_Bot.bat)")
    print("=" * 60 + "\n")
    
    # This is what the scheduler calls
    await pipeline_job()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED - Check Telegram for message")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
