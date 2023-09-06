import openai
import aiofiles

from config_file import OPEN_AI_API

openai.api_key = OPEN_AI_API

async def start_data():
    async with aiofiles.open('gpt_pattern.txt', encoding='utf8') as f:
        lines = await f.read()
        return lines
        
async def answer_information(question = None):

    data = await start_data()
    messages = [{'role': 'system', 'content': f'''Remember the following information and give answers based on it. You are given data that contains possible questions after 
                 "Question:" and possible answers to them after "Answer:".\n{data}'''}]
    if question is not None:
        messages.append({'role': 'user', 'content': question})
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )

    chat_response = completion.choices[0].message.content
    messages.append({'role': 'assistant', 'content': chat_response})
    return chat_response