import openai
import aiofiles
from datetime import datetime

from config_file import OPEN_AI_API
from additional_functions import save_to_txt

openai.api_key = OPEN_AI_API

async def start_data():
    async with aiofiles.open('chat_gpt.txt', encoding='utf8') as f:
        lines = await f.read()
        return lines
        
async def answer_information(question = None):
    data = await start_data()
    messages = [{'role': 'system', 
                 'content': f'''Remember the following information and give answers based on it. 
                 1) First, you are given data that contains possible questions after 
                 "Question:" and possible answers to them after "Answer".
                 2) Second, you must pay your attention on info-blocks caged between following symbols:
                 "----------------I-N-F-O-B-L-O-C-K----------------". These blocks contain general info 
                 which could be useful addition to your generated answer."
                 
                 You must generate your answer on russian language!
                 Try to fit the answer into no more than 2 paragraphs!
                 Try to structurize your answer.
                 \n{data}'''}]
    if question is not None:
        messages.append({'role': 'user', 'content': question})
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )

    chat_response = completion.choices[0].message.content
    messages.append({'role': 'assistant', 'content': chat_response})
    current_date = datetime.now().strftime(r'%Y-%m-%d') ; current_time = datetime.now().time()
    save_to_txt(logs=f"""{current_date} {current_time}: Текущие траты токенов на входные данные - {completion['usage']['prompt_tokens']}
{current_date} {current_time}: Текущие траты токенов на выходные данные - {completion['usage']['completion_tokens']}
""")
    return chat_response, completion['usage']['total_tokens']