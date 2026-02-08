import asyncio
import httpx
import json
import time

TOKEN = "8552436736:AAEqDFJ7oO9AyoMMe8cNdldnOOzBRlAvYyU"

async def monitor_chat_id():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    print(f"Monitoring updates for 60 seconds...")
    
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        offset = 0
        
        while time.time() - start_time < 60:
            try:
                resp = await client.get(url, params={"offset": offset}, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                
                updates = data.get("result", [])
                if updates:
                    last_update = updates[-1]
                    offset = last_update["update_id"] + 1
                    
                    message = last_update.get("message") or last_update.get("my_chat_member")
                    if message:
                        chat = message.get("chat", {})
                        chat_id = chat.get("id")
                        title = chat.get("title", "Private")
                        
                        print(f"\n✅ CAPTURED Chat ID: {chat_id} ({title})")
                        with open("chat_id.txt", "w") as f:
                            f.write(str(chat_id))
                        return
                    
            except Exception as e:
                print(f"Error: {e}")
            
            await asyncio.sleep(2)
            
    print("Timeout. No message received.")

if __name__ == "__main__":
    if asyncio.get_event_loop_policy().__class__.__name__ == 'WindowsProactorEventLoopPolicy':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(monitor_chat_id())
