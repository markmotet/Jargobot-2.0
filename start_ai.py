from whisper_transcribe import transcribe_with_whisper
from record_audio import record_audio
from eleven_labs import send_to_eleven_labs
from chatgpt import send_to_chatgpt
from play_audio import play_audio
from voices_dictionary import voices_dictionary

message_list = [
            {"role": "system", "content": voices_dictionary['Nazeem'][1]},
        ]

while(True):

    # User response
    input("\nPress Enter to start recording...")
    record_audio() # Saves recording to output.wav
    print('Transcribing...')
    recording_transcription = transcribe_with_whisper("./output.wav")
    print('\n---------------------------------')
    print('Transcription: ' + recording_transcription)
    print('---------------------------------')
    message_list.append({"role": "user", "content": recording_transcription})
    
    # AI Response
    print('\nSending to ChatGPT...')
    chat_gpt_response = send_to_chatgpt(message_list)
    print('\nSending to ElevenLabs...\n')
    send_to_eleven_labs(chat_gpt_response, voices_dictionary['Nazeem'][0])  
    message_list.append({"role": "assistant", "content": chat_gpt_response})
    for message in message_list:
        print(message['role'] + ': ' + message['content'])
    play_audio('./audio.mp3')



        

    

