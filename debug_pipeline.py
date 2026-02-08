import asyncio
import logging
import sys
import traceback

# Redirect output
sys.stdout = open("pipeline_debug.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

logging.basicConfig(level=logging.INFO)

async def trigger():
    print("🚀 Triggering pipeline...")
    try:
        from src.app.core.scheduler import pipeline_job
        await pipeline_job()
        print("✅ Pipeline finished.")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(trigger())
