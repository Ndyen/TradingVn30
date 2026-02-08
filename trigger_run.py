import asyncio
import logging
import sys

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def trigger():
    print("🚀 Triggering immediate analysis pipeline...")
    try:
        from src.app.core.scheduler import pipeline_job
        await pipeline_job()
        print("✅ Pipeline execution finished.")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(trigger())
