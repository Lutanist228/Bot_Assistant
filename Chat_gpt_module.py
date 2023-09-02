import openai

# from config import OPEN_AI_API

async def start_data():
    async with open('boltun.txt', encoding='utf8') as f:
        lines = f.read()
        print(lines)
        
