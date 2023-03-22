import requests

AUDIO_FILE_PATH = './audio.mp3'

class UnauthorizedError(Exception):
    pass

def text_to_speech(input_text, voice_id, api_key, audio_file_path=AUDIO_FILE_PATH):
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
        with open(audio_file_path, 'wb') as f:
            f.write(response.content)
    elif response.status_code == 401:
        raise UnauthorizedError("Unauthorized access. Please check your API key.")

    else:
        print('Request failed with status code', response.status_code)

def get_voices(api_key):
    headers = {
        'accept': 'application/json',
        'xi-api-key': api_key
    }

    response = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)

    if response.status_code == 200:
        voices = response.json()
        non_premade_voices = [voice for voice in voices['voices'] if voice['category'] != 'premade']
        return {'voices': non_premade_voices}
    elif response.status_code == 401:
        raise UnauthorizedError("Unauthorized access. Please check your API key.")
    else:
        print('Request failed with status code', response.status_code)
        return None


# --------------------------------------------
# voices = get_voices(api_key)
# if voices:
#     print(voices)
# --------------------------------------------


def get_voice_metadata(voice_id, api_key, with_settings=False):
    headers = {
        'accept': 'application/json',
        'xi-api-key': api_key
    }

    params = {
        'with_settings': with_settings
    }

    response = requests.get(f'https://api.elevenlabs.io/v1/voices/{voice_id}', headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise UnauthorizedError("Unauthorized access. Please check your API key.")
    else:
        print('Request failed with status code', response.status_code)
        return None

# --------------------------------------------
# voice_id = "EtpTxhKmm9VLwqbfnO6e"
# with_settings = True

# voice_metadata = get_voice_metadata(voice_id, api_key, with_settings)

# if voice_metadata:
#     print(voice_metadata)
# --------------------------------------------

def add_voice(api_key, name: str, file_url: str, labels: str = None):
    headers = {
        'xi-api-key': api_key
    }

    data = {
        'name': name,
    }

    if labels:
        data['labels'] = labels

    # pass the file content from the URL directly to the files parameter as a stream
    response = requests.get(file_url, stream=True)
    files_data = [('files', (file_url.split('/')[-1], response.raw))]
    
    response = requests.post('https://api.elevenlabs.io/v1/voices/add', headers=headers, data=data, files=files_data)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise UnauthorizedError("Unauthorized access. Please check your API key.")
    else:
        print('Request failed with status code', response.status_code)
        return None

# --------------------------------------------
# name = 'Genji'
# file_url = 'https://cdn.discordapp.com/attachments/747284361619046512/1087872086686572734/Genji.ogg'
# response = add_voice(api_key, name, file_url)
# if response:
#     print('Voice added successfully')
# else:
#     print('Failed to add voice')
# --------------------------------------------


def delete_voice(voice_id, api_key):
    headers = {
        'accept': 'application/json',
        'xi-api-key': api_key
    }

    response = requests.delete(f'https://api.elevenlabs.io/v1/voices/{voice_id}', headers=headers)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise UnauthorizedError("Unauthorized access. Please check your API key.")
    else:
        print('Request failed with status code', response.status_code)
        return None
    

# --------------------------------------------
# voice_id = "jUIBGoVkXJ48MPgdR188"

# result = delete_voice(voice_id, api_key)

# if result:
#     print(result)
# --------------------------------------------