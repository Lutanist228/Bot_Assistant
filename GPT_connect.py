import openai

GPT_API = "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"
openai.api_key = GPT_API

def sending_pattern(role, gpt_pattern):
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": role, "content": gpt_pattern}
    ]
    )

def extracting_reply(role, message_text):
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": role, "content": message_text}
    ]
    )
    
    return completion.choices[0].message.content

