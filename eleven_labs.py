import requests

AUDIO_FILE_PATH = './audio.mp3'

def send_to_eleven_labs(input_text, voice_id, api_key, audio_file_path=AUDIO_FILE_PATH):
    headers = {
        'accept': 'audio/mpeg',
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }

    data = {
        'text': input_text,
        'voice_settings': {
            'stability': 0.4,
            'similarity_boost': 1.0
        }
    }

    response = requests.post('https://api.elevenlabs.io/v1/text-to-speech/{}'.format(voice_id), headers=headers, json=data, stream=True)

    if response.status_code == 200:
        with open(AUDIO_FILE_PATH, 'wb') as f:
            f.write(response.content)
        # print('Audio file saved:', AUDIO_FILE_PATH)

    else:
        print('Request failed with status code', response.status_code)