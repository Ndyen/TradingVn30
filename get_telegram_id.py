import asyncio
import httpx
import json

TOKEN = "8552436736:AAEqDFJ7oO9AyoMMe8cNdldnOOzBRlAvYyU"

async def get_chat_id():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    print(f"Checking updates from: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("ok"):
                print("Error from Telegram API:", data)
                return

            updates = data.get("result", [])
            if not updates:
                print("No updates found. Please send a message to the bot first.")
                return

            # Find the last message
            last_update = updates[-1]
            message = last_update.get("message") or last_update.get("my_chat_member")
            
            if message:
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                chat_type = chat.get("type")
                chat_title = chat.get("title", "Private")
                
                print(f"\n✅ Found Chat ID: {chat_id}")
                print(f"Type: {chat_type}")
                print(f"Title: {chat_title}")
                
                # Write to file for easy reading
                with open("chat_id.txt", "w") as f:
                    f.write(str(chat_id))
            else:
                print("Could not parse message from update:", json.dumps(last_update, indent=2))

        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    if asyncio.get_event_loop_policy().__class__.__name__ == 'WindowsProactorEventLoopPolicy':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_chat_id())
