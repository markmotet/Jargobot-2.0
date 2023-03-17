from pydub import AudioSegment
from pydub.playback import play

def play_audio(filename):
    audio = AudioSegment.from_file(filename, format="mp3")
    play(audio)