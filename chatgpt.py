import openai

def send_to_chatgpt(api_key, message_list):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_list
    )

    return response['choices'][0]['message']['content']
